
=============
ckanext-faociok
=============

- GUI customization
- M49 vocabulary
- Dataset schema customization and faceting
  - Datatype
  - M49 region indexing
- Scripts for creating default groups

------------
Requirements
------------

...

------------
Installation
------------

To install ckanext-faociok:

#. Activate your CKAN virtual environment, for example::

     . /usr/lib/ckan/default/bin/activate

#. Install the ckanext-faociok Python package into your virtual environment::

     pip install ckanext-faociok

#. Add ``faociok`` to the ``ckan.plugins`` setting in your CKAN
   config file (by default the config file is located at
   ``/etc/ckan/default/production.ini``).

#. Update the DB using the ``initdb`` command::
 
     paster --plugin=ckanext-faociok faociok initdb --config=/etc/ckan/default/production.ini
     
#. Load the M49 vocabulary::

     paster --plugin=ckanext-faociok vocabulary import_m49 files/M49_Codes.xlsx --config=/etc/ckan/default/production.ini

#. Load the datatypes codelist::

     paster --plugin=ckanext-faociok vocabulary load datatype files/faociok.datatype.csv  --config=/etc/ckan/default/production.ini     

#. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu::

     sudo service apache2 reload

   If CKAN is managed through supervisor::

     systemctl restart supervisord 

#. Update SOLR schema.xml and add field:

.. code::

   <dynamicField name="fao_m49_regions*" type="string" multiValued="true" indexed="true" stored="false"/>
   
#. Restart SOLR


------------------------
Development Installation
------------------------

To install ckanext-faociok for development, activate your CKAN virtualenv and
do::

    git clone https://github.com/geosolutions-it/ckanext-faociok.git
    cd ckanext-faociok
    python setup.py develop
    pip install -r dev-requirements.txt


-----------------
Running the Tests
-----------------

To run the tests, do::

    nosetests --nologcapture --with-pylons=test.ini

To run the tests and produce a coverage report, first make sure you have
coverage installed in your virtualenv (``pip install coverage``) then run::

    nosetests --nologcapture --with-pylons=test.ini --with-coverage --cover-package=ckanext.faociok --cover-inclusive --cover-erase --cover-tests

