=============
ckanext-datadotworld
=============

With this extension enabled, organization manage section has additional tab
`data.world`, where you can specify syncronization options.

------------
Requirements
------------

For example, you might want to mention here which versions of CKAN this
extension works with.

------------------
Supported versions
------------------

All CKAN versions from version 2.4(including 2.7).

All versions support celery backend but version 2.7 allows to use RQ instead.
There are no any particular changes in order to use new backend - just start
it using::

    paster --plugin=ckan jobs worker -c /config.ini

instead of::

    paster celeryd run -c /config.ini

Details at http://docs.ckan.org/en/latest/maintaining/background-tasks.html

------------
Installation
------------

.. Add any additional install steps to the list below.
   For example installing any non-Python dependencies or adding any required
   config settings.

To install ckanext-datadotworld:

1. Activate your CKAN virtual environment, for example::

     . /usr/lib/ckan/default/bin/activate

2. Install the ckanext-datadotworld Python package into your virtual environment::

     pip install ckanext-datadotworld

3. Add ``datadotworld`` to the ``ckan.plugins`` setting in your CKAN
   config file (by default the config file is located at
   ``/etc/ckan/default/production.ini``).

4. Create DB tables::

     paster datadotworld init -c /config.ini
     paster datadotworld upgrade -c /config.ini

5. Start celery daemon either with suprevisor or using paster::

     paster celeryd run -c /config.ini


---------------
Config Settings
---------------

Attempts to push failed datasets can be sceduled by adding line to cron::

    * 8 * * * paster --plugin=ckanext-datadotworld datadotworld push_failed -c /config.ini

Similar solution allows to syncronize remote(not uploaded) resources with data.world::

    * 8 * * * paster --plugin=ckanext-datadotworld datadotworld sync_resources -c /config.ini

------------------------
Development Installation
------------------------

To install ckanext-datadotworld for development, activate your CKAN virtualenv and
do::

    git clone https://github.com/datadotworld/ckanext-datadotworld.git
    cd ckanext-datadotworld
    python setup.py develop
    pip install -r dev-requirements.txt
    paster datadotworld init -c /config.ini

-----------------
Running the Tests
-----------------

To run the tests, do::

    nosetests --nologcapture --with-pylons=test.ini

To run the tests and produce a coverage report, first make sure you have
coverage installed in your virtualenv (``pip install coverage``) then run::

    nosetests --nologcapture --with-pylons=test.ini --with-coverage --cover-package=ckanext.datadotworld --cover-inclusive --cover-erase --cover-tests
