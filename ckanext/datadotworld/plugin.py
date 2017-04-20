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

    def after_create(self, context, pkg_dict):
        api.notify(pkg_dict, DomainObjectOperation.new)
        return pkg_dict

    def after_update(self, context, pkg_dict):
        api.notify(pkg_dict, DomainObjectOperation.changed)
        return pkg_dict

    def after_delete(self, context, pkg_dict):
        api.notify(pkg_dict, DomainObjectOperation.deleted)
        return pkg_dict
