#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import logging
import json

from ckan import plugins
from ckan.lib.i18n import get_lang
from ckan.lib.base import config
from ckan.plugins import toolkit as t
from ckanext.faociok import schema as s
from ckanext.faociok import helpers as h
from ckanext.faociok import validators as v
from ckanext.faociok.models import VocabularyTerm, Vocabulary

log = logging.getLogger(__name__)

# Configuration switch for trimming long text fields from harvester
# for solr. see:
# https://github.com/geosolutions-it/ckanext-faociok/pull/36#issuecomment-422344679
# alternatively you can declare field in solr schema manually as text (replace $field_name
# with actual field name):
#   <field name="$field_name" type="text" multiValued="false" indexed="true" stored="false"/>
# and set ckanext.faociok.trim_for_index to false. 
#
# default - true
CONFIG_TRIM_FOR_INDEX = 'ckanext.faociok.trim_for_index'

# get config val once
TRIM_FOR_INDEX = t.asbool(config.get(CONFIG_TRIM_FOR_INDEX, 'true'))
TRIM_LIMIT = 32 * 1024

# lists of known text type fields - those should not be trimmed, as they are expected to be long
TRIM_SKIP_FOR_FIELDS = "author author_email child_of dependency_of depends_on derives_from has_derivation linked_from links_to maintainer maintainer_email notes res_description res_name text title urls ckan_url download_url groups license maintainer name notes organization url data_dict validated_data_dict".split(' ')
TRIM_SKIP_FOR_FIELDS_WILDCHAR = 'extras_ res_extras_ vocab_'.split(' ')

class FaociokPlugin(plugins.SingletonPlugin, t.DefaultDatasetForm):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IDatasetForm)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IFacets, inherit=True)
    plugins.implements(plugins.IPackageController, inherit=True)

    # IConfigurer

    def update_config(self, config_):
        t.add_template_directory(config_, 'templates')
        t.add_public_directory(config_, 'public')
        t.add_resource('fanstatic', 'faociok')
        return config_

    # IDatasetForm

    def is_fallback(self):
        # Return True to register this plugin as the default handler for
        # package types not handled by any other IDatasetForm plugin.
        return True
        
    def package_types(self):
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        return []

    def create_package_schema(self):
        schema = super(FaociokPlugin, self).create_package_schema()
        schema.update(s.get_create_package_schema())
        self._update_schema(schema, 'convert_to_extras', before=False)
        return schema

    def update_package_schema(self):
        schema = super(FaociokPlugin, self).update_package_schema()
        schema.update(s.get_update_package_schema())
        self._update_schema(schema, 'convert_to_extras', before=False)
        return schema

    def show_package_schema(self):
        schema = super(FaociokPlugin, self).show_package_schema()
        schema.update(s.get_show_package_schema())
        self._update_schema(schema, 'convert_from_extras', before=True)
        return schema

    def _update_schema(self, schema, converter, before=False):
        for k in schema.keys():
            if k.startswith('fao_'):
                field = schema[k]
                if before:
                    schema[k] = [t.get_converter(converter)] + field
                else:
                    schema[k] = field + [t.get_converter(converter)]

        return schema

    # IValidators

    def get_validators(self):
        # remember, due to schema<->vocabulary dependency,
        # schema field should be constructed `fao_` + vocab name
        return {
            'fao_datatype': v.fao_datatype,
            'fao_m49_regions': v.fao_m49_regions,
        }

    # ITemplateHelpers

    def get_helpers(self):
        return {
            'get_faociok_vocabulary_items': h.get_vocabulary_items,
            #'get_faociok_vocabulary_items_raw': h.get_vocabulary_items_raw,
            'get_faociok_vocabulary_items_annotated': h.get_vocabulary_items_annotated,
            'get_faociok_package_schema': s._get_package_schema,
            'get_fao_datatype': h.get_fao_datatype,
            'get_fao_m49_region': h.get_fao_m49_region,
            'get_faociok_field_data': h.get_field_data,
            'get_fao_url_for_location': h.get_url_for_location,
            'load_json': h.load_json,
            'most_popular_groups': h.most_popular_groups,
            'get_fao_groups_featured': h.get_groups_featured,
            'get_fao_organizations_featured': h.get_organizations_featured,
            'get_fao_locations_featured': h.get_locations_featured,
        }

    # IFacets
    def dataset_facets(self, facets_dict, package_type):
        lang = get_lang()
        facets_dict['fao_datatype_{}'.format(lang)] = t._("Data type")
        for idx, l in ((0, t._("Regions"),),
                       (1, t._("Countries"),)):
            facets_dict['fao_m49_regions_l{}_{}'.format(idx, lang)] = l
        return facets_dict

    # IPackageController

    def get_localized_regions(self, regions):
        out = {'fao_m49_regions': regions}
        for reg in regions:
            v = VocabularyTerm.get(Vocabulary.VOCABULARY_M49_REGIONS, reg)
            parent = v
            while parent:
                for label in parent.labels:
                    lname = 'fao_m49_regions_l{}_{}'.format(parent.depth, label.lang)
                    try:
                        out[lname].add(label.label)
                    except KeyError:
                        out[lname] = set([label.label])
                parent = parent.parent
        for k,v in out.items():
            if isinstance(v, set):
                out[k] = list(v)
        return out

    def get_localized_datatype(self, datatype):
        out = {'fao_datatype': datatype}
        v = VocabularyTerm.get(Vocabulary.VOCABULARY_DATATYPE, datatype)
        for l in v.labels:
            lname = 'fao_datatype_{}'.format(l.lang)
            out[lname] = l.label
        return out

    def before_index(self, pkg_dict):
        
        regions = pkg_dict.get('fao_m49_regions')
        if regions:
            if not isinstance(regions, list):
                regions = v._deserialize_from_array(regions)
            localized_regions = self.get_localized_regions(regions)
            pkg_dict.update(localized_regions)
        if pkg_dict.get('fao_datatype'):
            localized_datatype = self.get_localized_datatype(pkg_dict['fao_datatype'])
            pkg_dict.update(localized_datatype)

        # optional trim values to 32k field size limit 
        if TRIM_FOR_INDEX:
            for k, val in pkg_dict.iteritems():
                # skip known text fields
                if k in TRIM_SKIP_FOR_FIELDS:
                    continue
                for fname in TRIM_SKIP_FOR_FIELDS_WILDCHAR:
                    if k.startswith(fname):
                        continue
                if isinstance(val, basestring):
                    if len(val) > TRIM_LIMIT:
                        log.debug('triming %s to 32k: %s', k, val)
                    pkg_dict[k] = val[:TRIM_LIMIT] if val else val
                elif isinstance(val, (list, set, tuple,)):
                    if any([len(item) > TRIM_LIMIT for item in val if isinstance(item, basestring)]):
                        log.debug('triming %s to 32k: %s', k, val)
                    pkg_dict[k] = [item[:TRIM_LIMIT] if isinstance(item, basestring) else item for item in val]

        return pkg_dict
