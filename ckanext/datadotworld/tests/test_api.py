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

"""Tests for plugin.py."""
import ckan.model as model
from ckan.tests.factories import Dataset, Organization, User
from ckanext.datadotworld.model.credentials import Credentials
from ckanext.datadotworld.model.extras import Extras
import ckanext.datadotworld.api as api
from ckan.tests.helpers import (
    reset_db
)
from ckanext.datadotworld.model import States
from json import dumps, loads
from ckanext.datadotworld.command import DataDotWorldCommand
import mock
from unittest import TestCase
import os.path as path

API = api.API

BASE = path.basename(path.abspath(__file__)) + '../../'
cmd = DataDotWorldCommand(None)


class Response:
    def __init__(self, status_code=200, content={}):
        self.status_code = status_code
        self.content = dumps(content)

    def json(self):
        return loads(self.content)


def setup_module():
    reset_db()
    cmd.run(['init', '-c', BASE + 'test.ini'])
    cmd.run(['upgrade', '-c', BASE + 'test.ini'])


def teardown_module():
    cmd.run(['downgrade', '-c', BASE + 'test.ini'])
    pass


class TestAPI(TestCase):

    def test_get_context(self):
        context = api.get_context()
        self.assertIn('ignore_auth', context)
        self.assertTrue(context['ignore_auth'])

    def test_dataworld_name(self):
        self.assertEqual('name', api.dataworld_name('NaMe'))
        self.assertEqual('n-a-m-e', api.dataworld_name('  n  a  m  e  '))
        self.assertEqual('n-a-m-e', api.dataworld_name('--n--a--m--e--'))
        self.assertEqual('n-a-m-e', api.dataworld_name('- _-n-_  __--a-M-e-'))

    def test_datadotworld_tags_name_normalize(self):
        tags_list = [
            {'name': u'invalid tag'},
            {'name': u'ta'},
            {'name': u'tag1'},
            {'name': u'tags'},
            {'name': u'valid tag'},
            {'name': u'\u0442\u0435\u0441\u0442'}]
        self.assertEqual(5, len(api.datadotworld_tags_name_normalize(tags_list)))
        tags_list = [
            {'name': u'invalid-tag'},
            {'name': u'taasdasdasdasdasdasdasdasdasdasdasdasdasdasdasdasdasd'},
            {'name': u'tag1'},
            {'name': u'TAGS'},
            {'name': u'invalid tag'}]
        self.assertEqual(3, len(api.datadotworld_tags_name_normalize(tags_list)))

    def test_get_creds_if_must_sync(self):
        pkg = Dataset()
        creds = api._get_creds_if_must_sync(pkg)
        self.assertEqual(None, creds)

        pkg = Dataset(owner_org=self.org['id'])
        creds = api._get_creds_if_must_sync(pkg)
        self.assertNotEqual(None, creds)

        old_creds = creds
        creds.integration = False
        creds = api._get_creds_if_must_sync(pkg)
        self.assertEqual(None, creds)

        old_creds.integration = True

    @mock.patch(api.__name__ + '.API.sync')
    def test_notify(self, sync):
        pkg = Dataset(type='related-dataset')
        self.assertFalse(api.notify(pkg['id']))

        pkg = Dataset()
        self.assertFalse(api.notify(pkg['id']))

        pkg = Dataset(owner_org=self.org['id'], state='draft')
        self.assertFalse(api.notify(pkg['id']))

        pkg = Dataset(owner_org=self.org['id'], state='deleted')
        self.assertTrue(api.notify(pkg['id']))

        pkg = Dataset(owner_org=self.org['id'])
        attempt = 0
        self.assertTrue(api.notify(pkg['id']))
        sync.assert_called_with(pkg, attempt)

    def test_prepare_resource_url(self):
        res = {'url': 'a/b/c.csv', 'name': 'File'}
        expect = {
            'name': 'File.csv',
            'source': {'expandArchive': True, 'url': res['url']}}
        self.assertEqual(expect, api._prepare_resource_url(res))

        res = {'url': 'a/b/c.csv', 'name': '', 'description': 'xxx'}
        expect = {
            'name': 'c.csv',
            'description': 'xxx',
            'source': {'expandArchive': True, 'url': res['url']}}
        self.assertEqual(expect, api._prepare_resource_url(res))

        res = {'url': 'a/b/c.csv', 'name': None}
        expect = {
            'name': 'c.csv',
            'source': {'expandArchive': True, 'url': res['url']}}
        self.assertEqual(expect, api._prepare_resource_url(res))

    def test_assert_description_truncation(self):
        res = {'url': 'a/b/c.csv', 'name': 'File', 'description': 'aaa'}
        truncated = api._prepare_resource_url(res)['description']
        self.assertEqual('aaa', truncated)

        res['description'] = 'a' * 120
        truncated = api._prepare_resource_url(res)['description']
        self.assertEqual('a' * 120, truncated)

        res['description'] = 'a' * 130
        truncated = api._prepare_resource_url(res)['description']
        self.assertEqual('a' * 117 + '...', truncated)

        res['description'] = 'a' * 110 + ' ' + 'b' * 10
        truncated = api._prepare_resource_url(res)['description']
        self.assertEqual('a' * 110 + '...', truncated)

    def test_prepared_resources_names(self):
        res = {'url': 'a/b/c.csv', 'name': 'File'}
        expect = 'File.csv'
        self.assertEqual(expect, api._prepare_resource_url(res)['name'])

        res = {'url': 'a/b/c.csv?a=1', 'name': 'File'}
        expect = 'File.csv'
        self.assertEqual(expect, api._prepare_resource_url(res)['name'])

        res = {'url': 'a/b/c.csv#hash', 'name': 'File'}
        expect = 'File.csv'
        self.assertEqual(expect, api._prepare_resource_url(res)['name'])

        res = {'url': 'a/b/c.csv', 'name': 'File', 'format': 'XML'}
        expect = 'File.xml'
        self.assertEqual(expect, api._prepare_resource_url(res)['name'])

        res = {'url': 'a/b/c.csv', 'name': 'File.xml'}
        expect = 'File.xml'
        self.assertEqual(expect, api._prepare_resource_url(res)['name'])

        res = {'url': 'a/b/c.csv', 'name': 'File.png', 'format': 'XML'}
        expect = 'File.xml'
        self.assertEqual(expect, api._prepare_resource_url(res)['name'])

    def test_generate_link(self):
        self.assertEqual(API.root + '/x', API.generate_link('x'))
        self.assertEqual(API.root + '/x/y', API.generate_link('x', 'y'))

    def test_creds_from_id(self):
        self.assertEqual(None, API.creds_from_id('x'))
        self.assertEqual(self.creds, API.creds_from_id(self.org['id']))

    def test_default_headers(self):
        headers = self.api._default_headers()
        self.assertIn('Authorization', headers)
        self.assertIn('Content-type', headers)
        self.assertIn('User-Agent', headers)
        self.assertEqual('application/json', headers['Content-type'])
        key = API.auth.format(key=self.creds.key)
        self.assertEqual(key, headers['Authorization'])

    @mock.patch('requests.get')
    def test_get(self, get):
        self.api._get('url')
        headers = self.api._default_headers()
        get.assert_called_once_with(url='url', headers=headers)

    @mock.patch('requests.post')
    def test_post(self, post):
        self.api._post('url', {'a': 1})
        headers = self.api._default_headers()
        data = '{"a": 1}'
        post.assert_called_once_with(url='url', headers=headers, data=data)

    @mock.patch('requests.put')
    def test_put(self, put):
        self.api._put('url', {'a': 1})
        headers = self.api._default_headers()
        data = '{"a": 1}'
        put.assert_called_once_with(url='url', headers=headers, data=data)

    @mock.patch('requests.delete')
    def test_delete(self, delete):
        self.api._delete('url', {'a': 1})
        headers = self.api._default_headers()
        data = '{"a": 1}'
        delete.assert_called_once_with(url='url', headers=headers, data=data)

    def test_format_data(self):
        pkg = Dataset(tags=[{'name': 'xx'}])
        result = self.api._format_data(pkg)
        expect = {
            'files': [],
            'description': pkg['title'],
            'license': 'Other',
            'tags': ['xx'],
            'title': pkg['name'],
            'visibility': 'OPEN',
            'summary': pkg['notes']}
        self.assertEqual(expect, result)

    def test_is_dict_changed(self):
        old = {'x': [{'e': 0}]}
        new = {'x': [{'e': 1}]}
        self.assertTrue(self.api._is_dict_changed(new, old))
        self.assertFalse(self.api._is_dict_changed(new, new))
        self.assertFalse(self.api._is_dict_changed(old, old))

    @mock.patch(api.__name__ + '.API._put')
    def test_create_request(self, method):
        data = {'a': 1}
        url = self.api.api_create_put.format(owner=self.api.owner, id='id')

        method.return_value = Response()
        self.api._create_request(data, 'id')
        method.assert_called_once_with(url, data)

        method.reset_mock()
        method.return_value = Response(404)
        self.api._create_request(data, 'id')
        method.assert_called_once_with(url, data)

    @mock.patch(api.__name__ + '.API._put')
    def test_update_request(self, method):
        data = {'a': 1}
        url = self.api.api_update.format(owner=self.api.owner, name='id')

        method.return_value = Response()
        self.api._update_request(data, 'id')
        method.assert_called_once_with(url, data)

        method.reset_mock()
        method.return_value = Response(404)
        self.api._update_request(data, 'id')
        method.assert_called_once_with(url, data)

    @mock.patch(api.__name__ + '.API._get')
    def test_is_update_required(self, method):
        data = {'a': 1}
        url = self.api.api_update.format(owner=self.api.owner, name='id')

        method.return_value = Response(200, data)
        check = self.api._is_update_required(data, 'id')
        method.assert_called_once_with(url)
        self.assertFalse(check)

        method.reset_mock()
        method.return_value = Response(200, {'x': 2})
        check = self.api._is_update_required(data, 'id')
        method.assert_called_once_with(url)
        self.assertTrue(check)

        method.reset_mock()
        method.return_value = Response(404)
        check = self.api._is_update_required(data, 'id')
        method.assert_called_once_with(url)
        self.assertTrue(check)

    @mock.patch(api.__name__ + '.API._delete')
    def test_delete_request(self, method):
        data = {'a': 1}
        url = self.api.api_delete.format(owner=self.api.owner, id='id')

        method.return_value = Response()
        self.api._delete_request(data, 'id')
        method.assert_called_once_with(url, data)

        method.reset_mock()
        method.return_value = Response(404)
        self.api._delete_request(data, 'id')
        method.assert_called_once_with(url, data)

    @mock.patch(api.__name__ + '.API._create_request')
    def test_create(self, create):
        data = {'uri': 'xxx'}
        extras = Extras(id='id')

        create.return_value = Response(200, data)
        result = self.api._create(data, extras)
        create.assert_called_once_with(data, 'id')
        self.assertEqual(data, result)
        self.assertEqual(data['uri'], extras.id)
        self.assertEqual(States.uptodate, extras.state)

        extras.state = States.pending
        extras.id = 'id'
        create.reset_mock()
        create.return_value = Response(200, {})
        result = self.api._create(data, extras)
        create.assert_called_once_with(data, 'id')
        self.assertEqual(data, result)
        self.assertEqual('id', extras.id)
        self.assertEqual(States.uptodate, extras.state)

        extras.state = States.pending
        create.reset_mock()
        create.return_value = Response(404, {})
        result = self.api._create(data, extras)
        create.assert_called_once_with(data, 'id')
        self.assertEqual(data, result)
        self.assertEqual('id', extras.id)
        self.assertEqual(States.failed, extras.state)

        extras.state = States.pending
        create.reset_mock()
        create.return_value = Response(429, {})
        result = self.api._create(data, extras)
        create.assert_called_once_with(data, 'id')
        self.assertEqual(data, result)
        self.assertEqual('id', extras.id)
        self.assertEqual(States.pending, extras.state)

    @mock.patch(api.__name__ + '.API._is_update_required')
    @mock.patch(api.__name__ + '.API._create_request')
    @mock.patch(api.__name__ + '.API._update_request')
    def test_update(self, update, create, update_required):
        data = {'uri': 'xxx'}
        extras = Extras(id='id')

        update_required.return_value = False
        self.api._update(data, extras)
        self.assertEqual(None, extras.message)
        update_required.return_value = True

        update.return_value = Response(200, data)
        result = self.api._update(data, extras)
        update.assert_called_once_with(data, 'id')
        self.assertEqual(data, result)
        self.assertEqual(dumps(data), extras.message)
        self.assertEqual(States.uptodate, extras.state)

        extras.state = States.pending
        update.reset_mock()
        update.return_value = Response(404, data)
        create.return_value = Response(200, data)
        result = self.api._update(data, extras)
        create.assert_called_once_with(data, 'id')
        update.assert_called_once_with(data, 'id')
        self.assertEqual(data, result)
        self.assertEqual(States.uptodate, extras.state)

        extras.state = States.pending
        extras.id = 'id'
        update.reset_mock()
        create.reset_mock()
        update.return_value = Response(404, data)
        create.return_value = Response(404, data)
        result = self.api._update(data, extras)
        create.assert_called_once_with(data, 'id')
        update.assert_called_once_with(data, 'id')
        self.assertEqual(data, result)
        self.assertEqual(States.failed, extras.state)

        extras.state = States.pending
        update.reset_mock()
        update.return_value = Response(400, {})
        result = self.api._update(data, extras)
        update.assert_called_once_with(data, 'id')
        self.assertEqual(data, result)
        self.assertEqual(States.failed, extras.state)

        extras.state = States.pending
        update.reset_mock()
        update.return_value = Response(429, data)
        result = self.api._update(data, extras)
        update.assert_called_once_with(data, 'id')
        self.assertEqual(data, result)
        self.assertEqual(States.pending, extras.state)

    @mock.patch(api.__name__ + '.API._delete_request')
    def test_delete_dataset(self, delete):
        data = {'uri': 'xxx'}
        extras = Extras(id='id')

        delete.return_value = Response(200, data)
        result = self.api._delete_dataset(data, extras)
        delete.assert_called_once_with(data, 'id')
        self.assertEqual(data, result)

        extras.state = States.deleted
        delete.reset_mock()
        delete.return_value = Response(400, {})
        result = self.api._delete_dataset(data, extras)
        delete.assert_called_once_with(data, 'id')
        self.assertEqual(data, result)
        self.assertEqual(States.failed, extras.state)

        extras.state = States.pending
        delete.reset_mock()
        delete.return_value = Response(429, {})
        result = self.api._delete_dataset(data, extras)
        delete.assert_called_once_with(data, 'id')
        self.assertEqual(data, result)
        self.assertEqual(States.pending, extras.state)

    @mock.patch(api.__name__ + '.API._create')
    @mock.patch(api.__name__ + '.API._update')
    def test_sync(self, update, create):
        pkg = Dataset()

        self.api.sync(pkg)
        self.assertTrue(create.called)
        self.assertFalse(update.called)

        create.reset_mock()
        self.api.sync(pkg)
        self.assertFalse(create.called)
        self.assertTrue(update.called)

        update.reset_mock()
        pkg = Dataset(state='deleted')
        self.api.sync(pkg)
        self.assertFalse(create.called)
        self.assertFalse(update.called)

    @mock.patch(api.__name__ + '.API._get')
    def test_sync_resources(self, get):
        url = 'https://api.data.world/v0/datasets/owner/x/sync'
        self.api.sync_resources('x')
        get.assert_called_once_with(url)

    @mock.patch(api.__name__ + '.API._get')
    def test_check_credentials(self, get):
        get.return_value = Response(200)
        check = self.api.check_credentials()
        self.assertTrue(check)

        get.reset_mock()
        get.return_value = Response(401)
        check = self.api.check_credentials()
        self.assertFalse(check)

    @classmethod
    def setUpClass(cls):
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
        model.Session.commit()
        cls.org = org
        cls.creds = creds
        cls.user = user
        cls.api = api.API(creds.owner, creds.key)
