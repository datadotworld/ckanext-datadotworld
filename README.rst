=============
ckanext-datadotworld
=============

With this extension enabled, the manage view for organizations is provided with the additional tab
`data.world`. Within the data.world tab organization admins can specify syncronization options that will apply for that organization.

------------------
Supported versions
------------------

CKAN version 2.4 or greater (including 2.7).

All versions support celery backend, but version 2.7 will use RQ.
There are no changes required to use new backend - just start
it using::

	paster --plugin=ckan jobs worker -c /config.ini

instead of::

	paster celeryd run -c /config.ini

Details at http://docs.ckan.org/en/latest/maintaining/background-tasks.html

------------
Installation
------------

To install ckanext-datadotworld:

1. Activate your CKAN virtual environment, for example::

	. /usr/lib/ckan/default/bin/activate

2. Install the ckanext-datadotworld Python package into your virtual environment::

	pip install git+https://github.com/datadotworld/ckanext-datadotworld

3. Add ``datadotworld`` to the ``ckan.plugins`` setting in your CKAN config file (by default the config file is located at ``/etc/ckan/default/production.ini``).

4. Create DB tables::

	paster datadotworld init -c /config.ini
	paster datadotworld upgrade -c /config.ini

5. Start celery daemon either with suprevisor or using paster::

	paster celeryd run -c /config.ini


---------------
Config Settings
---------------

Attempts to push failed datasets can be scheduled by adding the following line to cron::

	* 8 * * * paster --plugin=ckanext-datadotworld datadotworld push_failed -c /config.ini

A similar solution enables syncronization with remote (i.e. not uploaded) resources with data.world::

	* 8 * * * paster --plugin=ckanext-datadotworld datadotworld sync_resources -c /config.ini

------------------------
Development Installation
------------------------

To install ckanext-datadotworld for development, activate your CKAN virtualenv and
do the following::

	git clone https://github.com/datadotworld/ckanext-datadotworld.git
	cd ckanext-datadotworld
	python setup.py develop
	pip install -r dev-requirements.txt
	paster datadotworld init -c /config.ini

-----------------
Running the Tests
-----------------

Make sure you follow the CKAN testing guide (http://docs.ckan.org/en/latest/contributing/test.html).
To run the tests, do the following::

    nosetests --ckan --nologcapture --with-pylons=test.ini

To run the tests and produce a coverage report, first make sure you have coverage installed in your virtualenv (``pip install coverage``) then run::

    nosetests --ckan --nologcapture --with-pylons=test.ini --with-coverage --cover-package=ckanext.datadotworld --cover-inclusive --cover-erase --cover-tests
