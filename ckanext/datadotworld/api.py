import json
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


def notify(pkg_dict, operation):
    owner_org = pkg_dict.get('owner_org')
    org = model.Group.get(owner_org)
    if org is None:
        return
    credentials = org.datadotworld_credentials
    if credentials is None or not credentials.integration:
        return

    api = API(credentials.owner, credentials.key)
    api.sync(pkg_dict)


def _prepare_resources(resources):
    """Convert list of resources to files_list for data.world.
    """
    files = []
    for res in resources:
        file = os.path.basename(res['url'])
        files.append(dict(
            name=file,
            source=dict(url=res['url'])
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
            log.error(res.content)
        return data

    def _update(self, pkg_dict, entity):
        data = self._format_data(pkg_dict)
        extras = entity.datadotworld_extras

        headers = self._default_headers()
        url = self.api_update.format(owner=self.owner, name=extras.id)
        res = requests.put(url, data=json.dumps(data), headers=headers)

        if res.status_code >= 400:
            log.error(res.content)
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
            tags=tags,
            license=licenses.get(pkg_dict.get('license_id'), 'Other'),
            visibility='PRIVATE' if pkg_dict.get('private') else 'OPEN'
        )
        files = _prepare_resources(pkg_dict.get('resources', []))
        if files:
            data['files'] = files
        return data
