import json
import logging
from webhelpers.text import truncate
import requests
from ckanext.datadotworld.model.extras import Extras
from ckan.lib.munge import munge_name
import ckan.model as model

log = logging.getLogger(__name__)
licenses = {
    'cc-by': 'CC-BY'
    'other-pd': 'Public Domain',
    'odc-pddl': 'PDDL',
    'cc-zero': 'CC-0',
    'odc-by': 'ODC-BY',
    'cc-by-sa': 'CC-BY-SA',
    'odc-odbl': 'ODC-ODbL',
    'cc-nc': 'CC BY-NC',
    # 'CC BY-NC-SA',
}


def notify(entity, operation):
    orgs = entity.get_groups('organization')
    if not orgs:
        return
    org = orgs[0]
    credentials = org.datadotworld_credentials
    if credentials is None or not credentials.integration:
        return
    api = API(credentials.owner, credentials.key)
    api.sync(entity)


class API:
    api_root = 'https://api.data.world/v0'
    api_create = api_root + '/datasets/{owner}'
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
        return data

    def _update(self, entity):
        data = self._format_data(entity)

        log.info('Update package')
        return data

    def _format_data(self, entity):
        tags = []
        if entity.tag_string:
            tags = entity.tag_string.split(',')
        data = dict(
            title=entity.title,
            description=truncate(entity.notes, 120),
            summary=entity.notes,
            tags=tags,
            license=licenses.get(entity.license_id, 'Other'),
            visibility='PRIVATE' if entity.private else 'OPEN'
        )
        return data
