# Copyright 2017 data.world, inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os.path
import logging

import requests
from bleach import clean
from markdown import markdown
from webhelpers.text import truncate

import ckan.model as model
from ckan.logic import get_action
from ckan.lib.munge import munge_name

from ckanext.datadotworld.model import States
from ckanext.datadotworld.model.extras import Extras
from ckanext.datadotworld import __version__
import re


log = logging.getLogger(__name__)
licenses = {
    'cc-by': 'CC-BY',
    'other-pd': 'Public Domain',
    'odc-pddl': 'PDDL',
    'cc-zero': 'CC-0',
    'odc-by': 'ODC-BY',
    'cc-by-sa': 'CC-BY-SA',
    'odc-odbl': 'ODC-ODbL',
    'cc-nc': 'CC BY-NC',
    # 'CC BY-NC-SA',
}


def get_context():
    return {'ignore_auth': True}


def dataworld_name(title):
    cleaned_title = ' '.join(title.split()).replace('_', '-').replace(' ', '-')
    return munge_name(
        '-'.join(filter(None, cleaned_title.split('-')))
    )


def datadotworld_tags_name_normalize(tags_list):
    tags_list = [tag['name'].lower().replace('-', ' ').replace('_', ' ')
                 for tag in tags_list if (len(tag['name']) > 1 and
                                          len(tag['name']) <= 25)]
    tagname_match = re.compile('^[a-z0-9]+( [a-z0-9]+)*$')
    tags_list = [tag for tag in tags_list if tagname_match.match(tag)]
    tags_list = list(set(tags_list))
    return tags_list


def _get_creds_if_must_sync(pkg_dict):
    owner_org = pkg_dict.get('owner_org')
    org = model.Group.get(owner_org)
    if org is None:
        return
    credentials = org.datadotworld_credentials
    if credentials is None or not credentials.integration:
        return
    return credentials


def notify(pkg_id):
    pkg_dict = get_action('package_show')(get_context(), {'id': pkg_id})
    if pkg_dict.get('type', 'dataset') != 'dataset':
        return False
    credentials = _get_creds_if_must_sync(pkg_dict)
    if not credentials:
        return False
    if pkg_dict.get('state') == 'draft':
        return False
    api = API(credentials.owner, credentials.key)
    api.sync(pkg_dict)
    return True


def _prepare_resource_url(res):
    """Convert list of resources to files_list for data.world.
    """
    link = res['url'] or ''
    name = res['name'] or ''
    if link is None or name is None:
        log.info('Undefined url or name: {0}'.format(res))
    link_name, link_ext = os.path.splitext(os.path.basename(link))
    file_name, file_ext = os.path.splitext(os.path.basename(name))

    existing_format = res.get('format')
    if existing_format:
        ext = '.' + existing_format.lower()
    elif file_ext:
        ext = file_ext
    else:
        ext = link_ext.split('#').pop(0).split('?').pop(0)

    prepared_data = dict(
        name=(file_name or link_name) + ext,
        source=dict(url=link)
    )
    description = res.get('description', '')

    if description:

        prepared_data['description'] = truncate(
            description, 120, whole_word=True)

    return prepared_data


class API:
    root = 'https://data.world'
    api_root = 'https://api.data.world/v0'
    api_create = api_root + '/datasets/{owner}'
    api_create_put = api_create + '/{id}'
    api_update = api_create + '/{name}'
    api_delete = api_create + '/{id}'
    api_res_create = api_update + '/files'
    api_res_sync = api_update + '/sync'
    api_res_update = api_res_create + '/{file}'
    api_res_delete = api_res_create + '/{file}'

    auth = 'Bearer {key}'
    user_agent_header = 'ckanext-datadotworld/' + __version__

    @classmethod
    def generate_link(cls, owner, package=None):
        """Create link to data.world dataset.
        """
        parts = [cls.root, owner]
        if package:
            parts.append(package)
        return '/'.join(parts)

    @staticmethod
    def creds_from_id(org_id):
        """Find data.world credentials by org id.
        """
        org = model.Group.get(org_id)
        if not org:
            return
        return org.datadotworld_credentials

    def __init__(self, owner, key):
        """Initialize client with credentials.
        """
        self.owner = owner
        self.key = key

    def _default_headers(self):
        return {
            'Authorization': self.auth.format(key=self.key),
            'Content-type': 'application/json',
            'User-Agent': self.user_agent_header
        }

    def _get(self, url):
        """Simple wrapper around GET request.
        """
        headers = self._default_headers()
        return requests.get(url=url, headers=headers)

    def _post(self, url, data):
        """Simple wrapper around POST request.
        """
        headers = self._default_headers()
        return requests.post(url=url, data=json.dumps(data), headers=headers)

    def _put(self, url, data):
        """Simple wrapper around PUT request.
        """
        headers = self._default_headers()
        return requests.put(url=url, data=json.dumps(data), headers=headers)

    def _delete(self, url, data):
        """Simple wrapper around DELETE request.
        """
        headers = self._default_headers()
        return requests.delete(url=url, data=json.dumps(data), headers=headers)

    def _format_data(self, pkg_dict):
        notes = pkg_dict.get('notes') or ''
        tags = datadotworld_tags_name_normalize(pkg_dict.get('tags', []))
        data = dict(
            title=pkg_dict['name'],
            description=pkg_dict['title'],
            summary=notes,
            tags=list(set(tags)),
            license=licenses.get(pkg_dict.get('license_id'), 'Other'),
            visibility='PRIVATE' if pkg_dict.get('private') else 'OPEN',
            files=[
                _prepare_resource_url(res)
                for res in pkg_dict['resources']
            ]
        )

        return data

    def _is_dict_changed(self, new_data, old_data):
        for key, value in new_data.items():
            if old_data.get(key) != value:
                return True
        return False

    def _create_request(self, data, id):
        url = self.api_create_put.format(owner=self.owner, id=id)
        res = self._put(url, data)
        if res.status_code == 200:
            log.info('[{0}] Successfuly created'.format(id))
        else:
            log.warn(
                '[{0}] Create package: {1}'.format(id, res.content))

        return res

    def _update_request(self, data, id):
        url = self.api_update.format(owner=self.owner, name=id)
        res = self._put(url, data)
        if res.status_code == 200:
            log.info('[{0}] Successfuly updated'.format(id))
        else:
            log.warn(
                '[{0}] Update package: {1}'.format(id, res.content))

        return res

    def _delete_request(self, data, id):
        url = self.api_delete.format(owner=self.owner, id=id)
        res = self._delete(url, data)
        if res.status_code == 200:
            log.info('[{0}] Successfuly deleted'.format(id))
        else:
            log.warn(
                '[{0}] Delete package: {1}'.format(id, res.content))

        return res

    def _is_update_required(self, data, id):
        url = self.api_update.format(owner=self.owner, name=id)
        remote_res = self._get(url)
        if remote_res.status_code != 200:
            log.warn(
                '[{0}] Unable to get package for dirty check:{1}'.format(
                    id, remote_res.content))
        else:
            remote_data = remote_res.json()
            if not self._is_dict_changed(data, remote_data):
                return False
        return True

    def _create(self, data, extras):
        res = self._create_request(data, extras.id)
        extras.message = res.content
        if res.status_code == 200:
            resp_json = res.json()
            if 'uri' in resp_json:
                new_id = os.path.basename(resp_json['uri'])
                extras.id = new_id

            extras.state = States.uptodate
        else:
            extras.state = States.failed
            log.error('[{0}] Create package failed: {1}'.format(
                extras.id, res.content))

        return data

    def _update(self, data, extras):
        if not self._is_update_required(data, extras.id):
            return data

        res = self._update_request(data, extras.id)
        extras.message = res.content

        if res.status_code == 200:
            extras.state = States.uptodate
        elif res.status_code == 404:
            log.warn('[{0}] Package not exists. Creating...'.format(
                extras.id))
            res = self._create(data, extras)
        else:
            extras.state = States.failed
            log.error('[{0}] Update package error:{1}'.format(
                extras.id, res.content))
        return data

    def _delete_dataset(self, data, extras):
        log.warn('[{0}] Try to delete'.format(extras.id))
        res = self._delete_request(data, extras.id)
        extras.message = res.content
        if res.status_code == 200:
            query = model.Session.query(Extras).filter(Extras.id == extras.id)
            query.delete()
            log.warn('[{0}] deleted from datadotworld_extras table'.format(
                extras.id))
        else:
            extras.state = States.failed
            log.error('[{0}] Delete package error:{1}'.format(
                extras.id, res.content))
        return data

    def sync(self, pkg_dict):
        entity = model.Package.get(pkg_dict['id'])
        pkg_dict = get_action('package_show')(get_context(), {'id': entity.id})
        data_dict = self._format_data(pkg_dict)

        extras = entity.datadotworld_extras
        pkg_state = pkg_dict.get('state')
        if pkg_state == 'deleted':
            action = self._delete_dataset
        else:
            action = self._update if extras and extras.id else self._create
        if not extras:
            extras = Extras(
                package=entity, owner=self.owner,
                id=data_dict['title'])
            model.Session.add(extras)
            extras.state = States.pending

        # TODO: remove next line or set level to debug
        log.warn('Performing {0} with {1}'.format(
            getattr(action, '__name__', action),
            pkg_dict['id']))

        try:
            model.Session.commit()
        except Exception as e:
            model.Session.rollback()
            log.error('[sync problem] {0}'.format(e))

        action(data_dict, extras)
        model.Session.commit()

    def sync_resources(self, id):
        url = self.api_res_sync.format(
            owner=self.owner,
            name=id
        )
        resp = self._get(url)
        msg = '{0} - {1:20} - {2}'.format(
            resp.status_code, id, resp.content
        )
        print(msg)
        log.info(msg)

    def check_credentials(self):
        url = self.api_update.format(
            owner=self.owner,
            name='definitely-fake-dataset-name'
        )
        resp = self._get(url)

        if resp.status_code == 401:
            return False
        return True
