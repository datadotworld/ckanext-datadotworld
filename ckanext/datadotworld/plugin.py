import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckanext.datadotworld.model.credentials import Credentials
import ckan.model as model
import logging
import ckanext.datadotworld.api as api
import ckanext.datadotworld.helpers as dh
from ckan.lib.celery_app import celery
import os
from pylons import config

log = logging.getLogger(__name__)


class DatadotworldPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)

    # ITemplateHelpers

    def get_helpers(self):
        return {
            'datadotworld_link': api.API.generate_link,
            'datadotworld_creds': api.API.creds_from_id,
            'datadotworld_admin_in_orgs': dh.admin_in_orgs
        }

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'datadotworld')

    # IRoutes

    def before_map(self, map):
        map.connect(
            'organization_dataworld',
            '/organization/edit/{id}/data.world',
            controller='ckanext.datadotworld.controller:DataDotWorldController',
            action='edit')
        map.connect(
            'list_dataworld_failed',
            '/data.world/failed',
            controller='ckanext.datadotworld.controller:DataDotWorldController',
            action='list_failed')

        return map

    # IPackageController

    def after_create(self, context, data_dict):
        ckan_ini_filepath = os.path.abspath(config['__file__'])
        celery.send_task(
            'datadotworld.syncronize',
            args=[data_dict['id'], ckan_ini_filepath])
        return data_dict

    def after_update(self, context, data_dict):
        ckan_ini_filepath = os.path.abspath(config['__file__'])
        celery.send_task(
            'datadotworld.syncronize',
            args=[data_dict['id'], ckan_ini_filepath])
        return data_dict
