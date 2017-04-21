"""Tests for plugin.py."""
import ckan.model as model
from ckan.model.types import make_uuid
from ckan.model.domain_object import DomainObjectOperation as DOO
import ckanext.datadotworld.plugin as plugin
from ckan.tests.helpers import call_action
from ckan.tests.factories import Dataset, Organization, User
from ckanext.datadotworld.model.credentials import Credentials
from ckanext.datadotworld.model.extras import Extras
from ckanext.datadotworld.model.resource import Resource
from ckan.tests.helpers import (
    call_action, reset_db
)
from ckanext.datadotworld.model import create_tables
from json import loads

import mock
from unittest import TestCase


class OKResponse:
    status_code = 200


def setup_module():
    reset_db()
    create_tables()


class TestAPI(TestCase):
    def setUp(self):
        user = User()
        org = Organization(users=[
            {'capacity': 'admin', 'name': user['name']}
        ])
        creds = Credentials(
            organization_id=org['id'],
            integration=True,
            key='key',
            owner='owner'
        )
        model.Session.add(creds)
        self.org = org
        self.creds = creds
        self.user = user

    def _get_data(self, shallow=False, **kwargs):
        data = dict(
            owner_org=self.org['id']
        )
        if not shallow:
            tags = [{'name': 'xxx'}]
            data['tags'] = tags
            data['title'] = 'Another  dataset'
            data['notes'] = 'n' * 130
            data['private'] = True
            data['license_id'] = 'cc-by'
        data.update(kwargs)
        return data

    def _get_extras(self):
        q = model.Session.query(Extras)
        return q.all()

    @mock.patch('requests.post')
    def test_create_data(self, post):
        data = self._get_data(True, name='test-dataset')

        call_action('package_create', {
            'user': self.user['name']
        }, **data)
        self.assertEqual(1, post.call_count)
        self.assertEqual(
            data['name'], loads(post.call_args[1]['data'])['title'])
        extr = self._get_extras()[-1]
        self.assertEqual(extr.id, data['name'])

        post.reset_mock()

        data = self._get_data(name='another-dataset')
        call_action('package_create', {
            'user': self.user['name']
        }, **data)
        args = loads(post.call_args[1]['data'])
        self.assertListEqual(
            args['tags'], map(lambda t: t['name'], data['tags']))
        self.assertEqual('PRIVATE', args['visibility'])
        self.assertEqual(data['notes'], args['summary'])
        self.assertEqual(data['notes'][:117] + '...', args['description'])
        self.assertEqual('CC-BY', args['license'])
        self.assertEqual(data['title'], args['title'])
        extr = self._get_extras()[-1]
        self.assertEqual(extr.id, data['title'].lower().replace('  ', '-'))

    @mock.patch('requests.patch')
    @mock.patch('requests.post')
    @mock.patch('requests.delete')
    def test_add_resources(self, delete, post, patch):
        pkg = Dataset(user=self.user, owner_org=self.org['id'])
        self.assertEqual(1, post.call_count)
        self.assertEqual(0, patch.call_count)
        res = call_action('resource_create', {
            'user': self.user['name']
        }, package_id=pkg['id'], url='test/file.csv')

        res = call_action('resource_update', {
            'user': self.user['name']
        }, id=res['id'], url='test/file2.csv')

        res = call_action('resource_delete', {
            'user': self.user['name']
        }, id=res['id'])

        self.assertEqual(3, post.call_count)
        self.assertEqual(3, patch.call_count)
        self.assertEqual(2, delete.call_count)
