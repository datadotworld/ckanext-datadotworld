import json
from collections import defaultdict
import logging
from webhelpers.text import truncate
import requests
from ckanext.datadotworld.model.extras import Extras
from ckanext.datadotworld.model.resource import Resource
from ckan.lib.munge import munge_name
import ckan.model as model
from ckan.logic import get_action
import os.path


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


def _get_creds_if_must_sync(pkg_dict):
    owner_org = pkg_dict.get('owner_org')
    org = model.Group.get(owner_org)
    if org is None:
        return
    credentials = org.datadotworld_credentials
    if credentials is None or not credentials.integration:
        return
    return credentials


def _info_from_pkg_id(id):
    pkg_dict = get_action('package_show')(None, {
        'id': id
    })
    credentials = _get_creds_if_must_sync(pkg_dict)
    api = None
    if credentials:
        api = API(credentials.owner, credentials.key)

    return pkg_dict, api


def create_resource(res_dict):
    pkg_dict, api = _info_from_pkg_id(res_dict['package_id'])
    if not api:
        return
    res = model.Resource.get(res_dict['id'])
    api.create_resource(res, pkg_dict)
    model.Session.commit()


def update_resource(res):
    pkg_dict, api = _info_from_pkg_id(res.package_id)
    if not api:
        return
    api.delete_resource(res, pkg_dict)
    api.create_resource(res, pkg_dict)


def delete_resource(res_dict):
    res = model.Resource.get(res_dict['id'])
    pkg_dict, api = _info_from_pkg_id(res.package_id)
    if not api:
        return
    api.delete_resource(res, pkg_dict)


def notify(pkg_dict, operation):

    credentials = _get_creds_if_must_sync(pkg_dict)
    if not credentials:
        return
    api = API(credentials.owner, credentials.key)
    api.sync(pkg_dict)


def _prepare_resource_url(link):
    """Convert list of resources to files_list for data.world.
    """

    file = os.path.basename(link)
    return dict(
        name=file,
        source=dict(url=link)
    )



def _prepare_resource_files(links):
    """Convert list of resources to files_list for data.world.
    """
    files = []
    for link in links:
        file = 'f_' + os.path.basename(link)
        files.append(dict(
            name=file,
            source=dict(url=link)
        ))
    return files


class API:
    root = 'https://data.world'
    api_root = 'https://api.data.world/v0'
    api_create = api_root + '/datasets/{owner}'
    api_update = api_create + '/{name}'
    api_res_create = api_update + '/files'
    api_res_update = api_res_create + '/{file}'
    api_res_delete = api_res_create + '/{file}'

    auth = 'Bearer {key}'

    def __init__(self, owner, key):
        """Initialize client with credentials.
        """
        self.owner = owner
        self.key = key

    def sync(self, pkg_dict):
        entity = model.Package.get(pkg_dict['id'])
        if entity.datadotworld_extras:
            self._update(pkg_dict, entity)
        else:
            self._create(pkg_dict, entity)

    @classmethod
    def generate_link(cls, owner, package=None):
        url = cls.root + '/' + owner
        if package:
            url += '/' + package
        return url

    @classmethod
    def creds_from_id(cls, org_id):
        org = model.Group.get(org_id)
        if not org:
            return
        return org.datadotworld_credentials

    def create_resource(self, res, pkg_dict):
        entity = model.Package.get(pkg_dict['id'])
        extras = entity.datadotworld_extras
        if not extras:
            return
        if res.url_type == 'upload':
            log.error('Uploaded resources not supported yet')
            return
        res_dict = get_action('resource_show')(None, {'id': res.id})
        source = _prepare_resource_url(res_dict['url'])
        data = {
            "files": [
                source
            ]
        }
        url = self.api_res_create.format(
            name=extras.id,
            owner=self.owner
        )
        headers = self._default_headers()
        response = requests.post(
            url, headers=headers, data=json.dumps(data))
        remote_res = Resource(resource=res, id=source['name'])
        log.info(json.dumps(headers))
        log.info(json.dumps(data))
        log.warn(url)
        model.Session.add(remote_res)

    def delete_resource(self, res, pkg_dict):
        entity = model.Package.get(pkg_dict['id'])
        extras = entity.datadotworld_extras
        if not extras:
            return
        remote_res = res.datadotworld_resource
        if not remote_res:
            return
        url = self.api_res_delete.format(
            name=extras.id,
            owner=self.owner,
            file=remote_res.id
        )
        headers = self._default_headers()
        response = requests.delete(url, headers=headers)
        model.Session.delete(remote_res)

    def _default_headers(self):
        return {
            'Authorization': self.auth.format(key=self.key),
            'Content-type': 'application/json'
        }

    def _create(self, pkg_dict, entity):
        data = self._format_data(pkg_dict)
        extras = Extras(package=entity, owner=self.owner)
        extras.id = munge_name(' '.join(data['title'].split()))

        headers = self._default_headers()
        url = self.api_create.format(owner=self.owner)
        res = requests.post(url, data=json.dumps(data), headers=headers)

        if res.status_code < 300:
            model.Session.add(extras)
        else:
            log.error('Create package:' + res.content)
        return data

    def _update(self, pkg_dict, entity):
        data = self._format_data(pkg_dict)
        extras = entity.datadotworld_extras

        headers = self._default_headers()
        url = self.api_update.format(owner=self.owner, name=extras.id)

        remote_res = requests.get(url, headers=headers)
        if remote_res.status_code != 200:
            log.error('Unable to get remote: ' + remote_res.content)
        else:
            remote_data = remote_res.json()
            for key, value in data.items():
                if remote_data.get(key) != value:
                    break
            else:
                return
        res = requests.patch(url, data=json.dumps(data), headers=headers)

        if res.status_code >= 400:
            log.error('Update package:' + res.content)
        return data

    def _format_data(self, pkg_dict):
        tags = []
        notes = pkg_dict.get('notes')
        for tag in pkg_dict.get('tags', []):
            tags.append(tag['name'])
        data = dict(
            title=pkg_dict['title'],
            description=truncate(notes, 120),
            summary=notes,
            tags=list(set(tags)),
            license=licenses.get(pkg_dict.get('license_id'), 'Other'),
            visibility='PRIVATE' if pkg_dict.get('private') else 'OPEN'
        )

        return data
