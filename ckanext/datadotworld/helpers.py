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

import ckan.model as model

def admin_in_orgs(name):
    user = model.User.get(name)
    if not user:
        return []
    return user.get_groups('organization', 'admin')

def compat_enqueue(name, fn, args=None):
    u'''
    Enqueue a background job using Celery or RQ.
    '''
    try:
        # Try to use RQ
        from ckan.lib.jobs import enqueue
        enqueue(fn, args=args)
    except ImportError:
        # Fallback to Celery
        from ckan.lib.celery_app import celery
        celery.send_task(name, args=args)

def load_config(ckan_ini_filepath):
	import os
	import paste.deploy
	config_abs_path = os.path.abspath(ckan_ini_filepath)
	conf = paste.deploy.appconfig('config:' + config_abs_path)
	import ckan
	ckan.config.environment.load_environment(conf.global_conf,
	                                         conf.local_conf)


def register_translator():
	# https://github.com/ckan/ckanext-archiver/blob/master/ckanext/archiver/bin/common.py
	# If not set (in cli access), patch the a translator with a mock, so the
	# _() functions in logic layer don't cause failure.
	from paste.registry import Registry
	from pylons import translator
	from ckan.lib.cli import MockTranslator
	if 'registery' not in globals():
	    global registry
	    registry = Registry()
	    registry.prepare()

	if 'translator_obj' not in globals():
	    global translator_obj
	    translator_obj = MockTranslator()
	    registry.register(translator, translator_obj)
	    
def syncronize(id, ckan_ini_filepath, attempt=0):
	from ckanext.datadotworld.api import notify
	load_config(ckan_ini_filepath)
	register_translator()
	notify(id, attempt)
