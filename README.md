[![Build Status](https://travis-ci.org/geosolutions-it/ckanext-faociok.svg?branch=master)](https://travis-ci.org/geosolutions-it/faociok)
[![Code Coverage](https://codecov.io/github/geosolutions-it/ckanext-faociok/coverage.svg?branch=master)](https://codecov.io/github/geosolutions-it/ckanext-faociok?branch=master)

# ckanext-faociok

- GUI customization
- M49 vocabulary
- Dataset schema customization and faceting
  - Datatype
  - M49 region indexing
  - AGROVOC integration
- Scripts for creating default groups

## Requirements

* CKAN 2.5+ (tested with CKAN 2.6.3)

### Other Extensions
* [ckanext-harvest](https://github.com/ckan/ckanext-harvest) (to provide a common harvesting framework for ckan extensions)
* [ckanext-ddi](https://github.com/geosolutions-it/ckanext-ddi) (to harvest NADA Catalogs)
* [ckanext-dcat](https://github.com/ckan/ckanext-dcat) (to expose and consume metadata from other catalogs using RDF documents serialized using DCAT)
* [ckanext-tableauview](https://github.com/geosolutions-it/ckanext-tableauview) (to display tableau vizzes in CKAN)
* [ckanext-geoview](https://github.com/ckan/ckanext-geoview) (to display geospatial files and services in CKAN)
* [ckanext-pdfview](https://github.com/ckan/ckanext-pdfview) (to provide a view plugin for PDF files using PDF.js)

## Provides

* `faociok` - Theme customization, schema fields:
    * `fao_datatype` describes area of interest of data
    * `fao_m49_region` normalized statistical regions from UN M.49 vocabulary
    * `fao_agrovoc` normalized terms for agriculture from FAO
* `faociok_nada_harvester` - NADA/DDI harvester which handles additional FAO schema fields.

## Installation

To install ckanext-faociok:

1. Activate your CKAN virtual environment, for example:

        . /usr/lib/ckan/default/bin/activate

2. Install the ckanext-faociok Python package into your virtual environment:

        cd ckanext-faociok
        pip install -r requirements.txt
        pip install -e .

3. Add ``faociok`` to the ``ckan.plugins`` setting in your CKAN
   config file (by default the config file is located at
   ``/etc/ckan/default/production.ini``).
   
4. Add the needed configuration properties to the ``production.ini`` file:

        ckanext.faociok.datatype = other
        ckanext.faociok.trim_for_index = true
        ckanext.faociok.datatype.fixed = true
        
   Enable only the supported languages:
   
       ## Internationalisation Settings
       ckan.locale_default = en
       ckan.locale_order = en es fr
       ckan.locales_offered = en es fr
       ckan.locales_filtered_out = en_GB

5. Update the DB using the ``initdb`` command:
 
        paster --plugin=ckanext-faociok faociok initdb --config=/etc/ckan/default/production.ini
     
6. Load the M49 vocabulary:

        paster --plugin=ckanext-faociok vocabulary import_m49 files/M49_Codes.xlsx --config=/etc/ckan/default/production.ini

7. Load the datatypes codelist:

        paster --plugin=ckanext-faociok vocabulary load datatype files/faociok.datatype.csv  --config=/etc/ckan/default/production.ini   

8. Load AGROVOC vocabulary. **Important note:** `clean_agrovoc.sh` script is used to clean agrovoc file from unused triplets, so amount of data to parse is lower. Without it, ingestion script would use far more memory and time to process rdf file:

        cd ckanext-faociok/files    
        wget http://agrovoc.uniroma2.it/agrovocReleases/agrovoc_2018-09-03_lod.nt.zip
        unzip agrovoc_2018-09-03_lod.nt.zip
        bash clean_agrovoc.sh agrovoc_2018-09-03_lod.nt
        paster --plugin=ckanext-faociok vocabulary import_agrovoc agrovoc_2018-09-03_lod.nt.clean.nt --config=/etc/ckan/default/production.ini

**note:** You can replace timestamp with newer release. Check for newer AGROVOC Releases at http://aims.fao.org/node/121112 and see http://aims.fao.org/vest-registry/vocabularies/agrovoc for general information about accessing AGROVOC.
Mind that AGROVOC contains lot of data (over 30000 terms and around 500000 translated labels). File parsing and import will take ~10-20 minutes, depending on your hardware.

You should be able to update AGROVOC vocabulary just by providing to the script new version of RDF (mind that it should be in .nt format) from provided URLs.

Internally, each ingestion invocation removes existing terms and replaces with full set of new ones. This is processed within one transaction in database, so there should be no side-effects in running application (except for small slowdown for time of parsing and inserting new terms).

After ingesting new version of AGROVOC, you should run Solr reindexing. This is because indexed data don't refer to labels directly, they use local copy from the moment of idexation. This can lead to problems like displaying outdated term names in facets. Reindexation will refresh that data. 
    
9. Update SOLR `schema.xml` and add fields:

       <dynamicField name="fao_m49_regions*" type="string" multiValued="true" indexed="true" stored="false"/>
       <dynamicField name="fao_agrovoc*" type="string" multiValued="true" indexed="true" stored="false"/>
   
10. Restart SOLR

11. Reindex data in solr (optional, if you're upgrading AGROVOC):

        paster --plugin=ckan search-index rebuild --config=/etc/ckan/default/production.ini

12. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu::

        sudo service apache2 reload

    If CKAN is managed through supervisor:

        systemctl restart supervisord 
        
## Install Other Extensions

### Harvest ([ckanext-harvest](https://github.com/ckan/ckanext-harvest))

This extension provides a common harvesting framework for ckan extensions and adds a CLI and a WUI to CKAN to manage harvesting sources and jobs.

Installation steps are described in the [extension's repository](https://github.com/ckan/ckanext-harvest#installation)

### DDI Harvester ([ckanext-ddi](https://github.com/geosolutions-it/ckanext-ddi))

FAO-CIOK extension comes with DDI harvester which will add FAO-CIOK-specific fields to dataset based on harvested data. Harvester is available as `faociok_nada_harvester`, and requires `ckanext-ddi extension <https://github.com/geosolutions-it/ckanext-ddi>` to be installed to run properly. This harvester is available as **FAO/NADA harvester for DDI**.

**note:** To fully benefit from this harvester, you should have all vocabularies imported.

#### Installation

To install ckanext-ddi:

1. Activate your CKAN virtual environment, for example:

        . /usr/lib/ckan/default/bin/activate

2. Install the ckanext-ddi Python package into your virtual environment:

        cd ckanext-ddi
        pip install -r requirements.txt
        pip install -e .
    
#### Configuration

1. Add `faociok_nada_harvester` to `ckan.plugins` in configuration:

        ckan.plugins = ... faociok_nada_harvester

2. Add DDI-specific configuration to your ckan configuration file:
    
        ckanext.ddi.default_license =
        ckanext.ddi.allow_duplicates = False
        ckanext.ddi.override_datasets = False

3. Set default datatype for datasets. This will populate `fao_dataset` field if it's missing.
    
        ckanext.faociok.datatype = other

4. Set if long fields should be trimmed (see **Deployment notes** below) during indexing. This is turned on by default, so you need to set value to `false` to disable fields trimming:

        ckanext.faociok.trim_for_index = true

5. Harvester should have at least following configuration content:

        {"access_type":""}

6. Restart CKAN

#### Vocabulary term migration

In case of a need of bulk change of one term to another for specific vocabulary, this can be done in the following way:

1. Run `vocabulary rename_term` command with name of vocabulary, old term and new term. Below an example of invocation:

    paster --plugin=ckanext-faociok vocabulary rename_term datatype monitoring other --config=/etc/ckan/default/production.ini

2. If needed, you can import new vocabulary data without old term. Again, below an example of invocation, assuming `faociok.dataty.ecsv` doesn't have `monitoring` term anymore:

    paster --plugin=ckanext-faociok vocabulary load datatype files/faociok.datatype.csv  --config=/etc/ckan/default/production.ini  

**note:** Both terms should be present in vocabulary during term migration.

#### Deployment notes

When using FAO/NADA harvester, some ddi-specific fields in dataset may be large (especially `sampling_procedure_notes`). This is rather unfrequent situation, but it may cause error during indexation in Solr. CKAN tries to put all fields from dataset into index, including extra fields, so those fields also qualify. However, default field type is string, which can hold up to 32k of text. See `Solr Fields Ref, StrField <https://lucene.apache.org/solr/guide/6_6/field-types-included-with-solr.html>`. This can cause exceptions during indexing. We suggest two approaches to manage this:

 * Trim text fields to 32k char limit.

   When dataset is indexed, fields are flattened, some values are processed before pushing them to Solr. Such object can have values trimmed, so they will match 32k chars limit. Original dataset stored in CKAN won't be affected. There's also a blacklist of fields that should not be trimmed. Note, that trimming will remove some parts of text from index, so not all phrases from dataset may be available for search.

   This is default strategy. 

 * Change type of fields on per-field basis (or set default type to `text`).

   This is less destructive method, but requires some configuration changes:
   
   1. set `ckanext.faociok.trim_for_index` to `false`.

   2. add following line to Solr `schema.xml`. Replace `$field_name` with actual field name, repeat for each field affected:

          <field name="$field_name" type="text" multiValued="false" indexed="true" stored="false"/>

### DCAT ([ckanext-dcat](https://github.com/ckan/ckanext-dcat))

This extension provides plugins that allow CKAN to expose and consume metadata from other catalogs using RDF documents serialized using DCAT. 

#### Installation

To install ckanext-dcat:

1. Activate your CKAN virtual environment, for example:

        . /usr/lib/ckan/default/bin/activate

2. Install the ckanext-dcat Python package into your virtual environment:

        cd ckanext-dcat
        pip install -r requirements.txt
        pip install -e .

#### Configuration

1. Add the required plugins to `ckan.plugins` in configuration:

        ckan.plugins = ... dcat dcat_json_interface dcat_rdf_harvester dcat_json_harvester

2. Configure the needed dcat extension proeprties:

        ckanext.dcat.rdf.profiles = euro_dcat_ap
        ckanext.dcat.base_uri = http://your_base_uri/
        ckanext.dcat.expose_subcatalogs = False
        ckanext.dcat.clean_tags = True
        
3. Restart CKAN
        
### Tableau Viewer ([ckanext-tableauview](https://github.com/geosolutions-it/ckanext-tableauview))

This extension contains a view plugin to display tableau vizzes in CKAN.

#### Installation

To install ckanext-tableauview:

1. Activate your CKAN virtual environment, for example:

        . /usr/lib/ckan/default/bin/activate

2. Install the ckanext-tableauview Python package into your virtual environment:

        pip install ckanext-tableauview

#### Configuration

1. Add the required plugins to `ckan.plugins` in configuration:

        ckan.plugins = ... tableau_view
        
2. Restart CKAN
        
### GeoView ([ckanext-geoview](https://github.com/ckan/ckanext-geoview))

This extension contains view plugins to display geospatial files and services in CKAN. 

#### Installation

To install ckanext-geoview:

1. Activate your CKAN virtual environment, for example:

        . /usr/lib/ckan/default/bin/activate

2. Install the ckanext-geoview Python package into your virtual environment:

        pip install ckanext-geoview

#### Configuration

1. Add the resource_proxy plugin to the ckan.plugins setting:

        ckan.plugins = ... resource_proxy 
        
2. Add the required plugins to `ckan.plugins` in configuration:

        ckan.plugins = ... geo_view geojson_view wmts_view 

3. Add the needed geoview configuration properties:

        ckan.views.default_views = ... geo_view geojson_view wmts_view
        ckanext.geoview.ol_viewer.formats = wms wfs gml arcgis_rest

3. Restart CKAN
        
### PDFView ([ckanext-pdfview](https://github.com/ckan/ckanext-pdfview))

This extension provides a view plugin for PDF files using PDF.js.

#### Installation

To install ckanext-pdfview:

1. Activate your CKAN virtual environment, for example:

        . /usr/lib/ckan/default/bin/activate

2. Install the ckanext-pdfview Python package into your virtual environment:

        pip install ckanext-pdfview

#### Configuration

1. Add the resource_proxy plugin to the ckan.plugins setting:

        ckan.plugins = ... resource_proxy 
        
2. Add the required plugins to `ckan.plugins` in configuration:

        ckan.plugins = ... pdf_view
        
3. Restart CKAN

**note:** The final plugins configuration list should be something like the following:

        ckan.plugins = stats text_view image_view recline_view pdf_view datastore resource_proxy geo_view geojson_view wmts_view tableau_view  harvest ckan_harvester dcat dcat_json_interface dcat_rdf_harvester dcat_json_harvester faociok faociok_nada_harvester
        
## Development Installation

To install ckanext-faociok for development, activate your CKAN virtualenv and
do:

        git clone https://github.com/geosolutions-it/ckanext-faociok.git
        cd ckanext-faociok
        python setup.py develop
        pip install -r dev-requirements.txt

## Running the Tests

To run the tests, do:

        nosetests --nologcapture --with-pylons=test.ini

To run the tests and produce a coverage report, first make sure you have
coverage installed in your virtualenv (``pip install coverage``) then run::

        nosetests --nologcapture --with-pylons=test.ini --with-coverage --cover-package=ckanext.faociok --cover-inclusive --cover-erase --cover-tests

