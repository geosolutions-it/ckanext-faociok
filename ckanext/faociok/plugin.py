#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import json
import ckan.plugins as plugins
from ckan.lib.i18n import get_lang
import ckan.plugins.toolkit as t
from ckanext.faociok import schema as s
from ckanext.faociok import helpers as h
from ckanext.faociok import validators as v
from ckanext.faociok.models import VocabularyTerm, Vocabulary


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

        for k in schema.keys():
            if k.startswith('fao_'):
                schema[k] += [t.get_converter('convert_to_extras')]
        return schema

    def update_package_schema(self):
        schema = super(FaociokPlugin, self).update_package_schema()
        schema.update(s.get_update_package_schema())
        
        for k in schema.keys():
            if k.startswith('fao_'):
                schema[k] += [t.get_converter('convert_to_extras')]

        return schema

    def show_package_schema(self):
        schema = super(FaociokPlugin, self).show_package_schema()
        schema.update(s.get_show_package_schema())
        for k in schema.keys():
            if k.startswith('fao_'):
                field = schema[k]
                schema[k] = [t.get_converter('convert_from_extras')] + field
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
            'load_json': h.load_json,

        }

    # IFacets
    def dataset_facets(self, facets_dict, package_type):
        facets_dict['fao_datatype'] = t._("Data type")
        lang = get_lang()
        for idx, l in enumerate([t._("M49 Level 1 Region"),
                                 t._("M49 Level 2 Region"),
                                 t._("M49 Country Level")]):
            facets_dict['fao_m49_regions_l{}_{}'.format(idx, lang)] = l
        return facets_dict

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
        return out

    def before_index(self, pkg_dict):
        if pkg_dict.get('fao_m49_regions'):
            regions = json.loads(pkg_dict['fao_m49_regions'])
            localized_regions = self.get_localized_regions(regions)
            pkg_dict.update(localized_regions)
        return pkg_dict
