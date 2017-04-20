"""Tests for plugin.py."""
from ckan.model.domain_object import DomainObjectOperation as DOO
import ckanext.datadotworld.plugin as plugin
from ckan.tests.factories import Dataset, Organization
from ckan.tests.helpers import (
    call_action, reset_db
)
from ckanext.datadotworld.model import create_tables

import mock
from unittest import TestCase

def setup_module():
    reset_db()
    create_tables()

class TestAPI(TestCase):
    #mock.patch('ckanext.datadotworld.api.create')
    def test_provided_data(self, create=None):
        org = Organization()
        Dataset(
            owner_org=org['id'],
            tags=[dict(name='aa'), dict(name='bb')])
