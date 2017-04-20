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
    entity = model.Package.get(pkg_dict['id'])
    orgs = entity.get_groups('organization')
    if not orgs:
        return
    org = orgs[0]
    credentials = org.datadotworld_credentials
    if credentials is None or not credentials.integration:
        return
    api = API(credentials.owner, credentials.key)
    api.sync(entity)
    api.sync_resources(entity.resources, entity)


class API:
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

    def sync(self, entity):
        if entity.datadotworld_extras:
            self._update(entity)
        else:
            self._create(entity)

    def sync_resources(self, resources, pkg):
        files = []
        remove_queue = []
        remote_resources = []

        for res_obj in resources:
            res = get_action('resource_show')(None, {'id': res_obj.id})
            sync_res = res_obj.datadotworld_resource
            if sync_res is None:
                sync_res = Resource(resource=res_obj)
                remote_resources.append(sync_res)
                pass
            elif sync_res.url != res['url']:
                remove_queue.append(os.path.basename(sync_res.url))
            else:
                continue
            file = os.path.basename(res['url'])
            files.append(dict(
                name=file,
                source=dict(url=res['url'])
            ))
            sync_res.url = res['url']
            sync_res.id = file

        if not files:
            return
        extras = pkg.datadotworld_extras
        data = json.dumps(dict(files=files))
        headers = self._default_headers()

        for f in remove_queue:
            requests.delete(
                self.api_res_delete.format(
                    owner=self.owner,
                    name=extras.id,
                    file=f
                ),
                headers=headers
            )
        res = requests.post(
            self.api_res_create.format(
                owner=self.owner,
                name=extras.id
            ),
            data=data,
            headers=headers
        )
        model.Session.add_all(remote_resources)

    def _default_headers(self):
        return {
            'Authorization': self.auth.format(key=self.key),
            'Content-type': 'application/json'
        }

    def _create(self, entity):
        data = self._format_data(entity)
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

    def _update(self, entity):
        data = self._format_data(entity)
        extras = entity.datadotworld_extras

        headers = self._default_headers()
        url = self.api_update.format(owner=self.owner, name=extras.id)
        res = requests.patch(url, data=json.dumps(data), headers=headers)

        if res.status_code >= 400:
            log.error(res.content)
        return data

    def _format_data(self, entity):
        tags = []
        tag_string = getattr(entity, 'tag_string', '')
        if tag_string:
            tags = tag_string.split(',')
        data = dict(
            title=entity.title,
            description=truncate(entity.notes, 120),
            summary=entity.notes,
            tags=tags,
            license=licenses.get(entity.license_id, 'Other'),
            visibility='PRIVATE' if entity.private else 'OPEN'
        )
        return data
