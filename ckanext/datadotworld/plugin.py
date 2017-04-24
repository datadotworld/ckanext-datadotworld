from ckan.model.domain_object import DomainObjectOperation
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckanext.datadotworld.model.credentials import Credentials
import ckan.model as model
import logging
import ckanext.datadotworld.api as api

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
            'datadotworld_creds': api.API.creds_from_id
        }

    # IConfigurer

    def update_config(self, config_):
        has_table = model.meta.engine.has_table(
            Credentials.__tablename__
        )
        if not has_table:
            log.fatal('Run `paster datadotworld create` first')

        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'datadotworld')

    # IRoutes

    def before_map(self, map):
        map.connect(
            'organization_dataworld',
            '/organization/edit/{id}/data.world',
            controller='ckanext.datadotworld.controller:DataDotWorldController',
            action='edit', ckan_icon='globe')
        return map

    # IPackageController

    def after_create(self, context, data_dict):
        api.notify(data_dict, DomainObjectOperation.new)
        return data_dict

    def after_update(self, context, data_dict):
        api.notify(data_dict, DomainObjectOperation.changed)
        return data_dict
