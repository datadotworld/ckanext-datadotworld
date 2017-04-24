from ckan.lib.celery_app import celery
from ckanext.datadotworld.api import notify
import os


def load_config(ckan_ini_filepath):
    import paste.deploy
    config_abs_path = os.path.abspath(ckan_ini_filepath)
    conf = paste.deploy.appconfig('config:' + config_abs_path)
    import ckan
    ckan.config.environment.load_environment(conf.global_conf,
                                             conf.local_conf)


@celery.task(name="datadotworld.syncronize")
def syncronize(id, ckan_ini_filepath):
    load_config(ckan_ini_filepath)
    notify(id)
