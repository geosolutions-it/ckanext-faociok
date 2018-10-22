#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ckan.plugins.toolkit as toolkit

import json
from ckan.lib.i18n import get_lang
from ckanext.faociok import validators as v
from ckan.plugins import toolkit as t
from ckan.lib import helpers as h
from ckan.lib.base import config
from ckanext.faociok.models import Vocabulary, VocabularyTerm

DEFAULT_LANG = config.get('ckan.locale_default')

# makes order of datatype in get_datatype_items in fixed order 
FAOCIOK_DATATYPE_FIXED = 'ckanext.faociok.datatype.fixed'

def get_fao_datatype(name):
    lang = get_lang()
    term = VocabularyTerm.get(Vocabulary.VOCABULARY_DATATYPE, name)
    label = term.get_label(lang) or term.get_label(DEFAULT_LANG) or term.get_label('en')
    return (label.label or term.name) if term else None


def get_fao_m49_region(name):
    lang = get_lang()
    term = VocabularyTerm.get(Vocabulary.VOCABULARY_M49_REGIONS, name)
    if term:
        label = term.get_label(lang) or term.get_label(DEFAULT_LANG) or term.get_label('en')
        return label.label
    return name

def get_fao_agrovoc_term(name):
    lang = get_lang()
    term = VocabularyTerm.get(Vocabulary.VOCABULARY_AGROVOC, name)
    if term:
        label = term.get_label(lang) or term.get_label(DEFAULT_LANG) or term.get_label('en')
        return label.label
    return name

def format_term(term, depth):
    return u'{}{}{}'.format('-' * depth, ' ' if depth else '', term)


def get_vocabulary_items(vocabulary_name, is_multiple=False, filters=None, order_by=None):
    return VocabularyTerm.get_terms(vocabulary_name,
                                    lang=get_lang(),
                                    is_multiple=is_multiple,
                                    filters=filters,
                                    order_by=order_by)


def load_json(value, fail=False):
    try:
        return json.loads(value)
    except (ValueError, TypeError,):
        if fail:
            raise
        return value


def most_popular_groups(n):
    '''Return a sorted list of the groups with the most datasets.'''
    # Get a list of all the site's groups from CKAN, sorted by number of
    # datasets.
    groups = toolkit.get_action('group_list')(
        data_dict={ 'all_fields': True})

    # Truncate the list to the n most popular groups only.
    groups = sorted(groups, key=lambda k: k['package_count'], reverse=True) 
    groups = groups[:n]
     

    return groups


def get_field_data(data, field, lang=None):
    if field.get('element') == 'agrovoc':
        values = v._deserialize_from_array(data)
        out = []
        lang = lang or get_lang()
        for val in values:
            if not val:
                continue
            term = VocabularyTerm.get(Vocabulary.VOCABULARY_AGROVOC, val)
            if not term:
                out.append(u'{}|{}'.format(val, val))
                continue
            label = term.get_label(lang)
            if not label:
                label = term.get_label('en') 
            out.append(u'{}|{}'.format(val, label.label or val))
        print('out', out)
        return out
        
    elif field.get('multiple'):
        return v._deserialize_from_array(data)
    else:
        return data


def get_vocabulary_items_annotated(vocabulary_name, is_multiple=False, filters=None):
    return VocabularyTerm.get_terms(vocabulary_name,
                                    lang=get_lang(),
                                    include_dataset_count=True,
                                    is_multiple=is_multiple,
                                    filters=filters)

def get_locations_featured():
    lang = get_lang()
    return VocabularyTerm.get_most_frequent_parent(Vocabulary.VOCABULARY_M49_REGIONS, lang=lang, multiple=True, limit=4)
    #return get_vocabulary_items_annotated('m49_regions', is_multiple=True, filters={'depth':0})[:4]


def get_groups_featured():
    return _get_featured('group')


def get_organizations_featured():
    return _get_featured('organization')


def _get_featured(group_type, max_results=4):
    params_with_pkg = {'limit': 4,
                       'all_fields': True,
                       'sort': 'package_count'}
    params_any = {'limit': 4, 'all_fields': True}
    call_name = '{}_list'.format(group_type)
    action = t.get_action(call_name)

    data = action({}, params_with_pkg)\
        or action({}, params_any)
    return data[:max_results]

def get_url_for_location(location_code):
    lang = get_lang()
    term = VocabularyTerm.get(Vocabulary.VOCABULARY_M49_REGIONS, location_code)
    if not term:
        return h.url_for('search')
    label = term.get_label(lang).label or term.get_label('en').label
    qdict = {'fao_m49_regions_l{}_{}'.format(term.depth, lang): label}
    return h.url_for('search', **qdict)


# defined by https://github.com/geosolutions-it/C013-FAO-CIOK-CKAN/issues/36
# National time Series, Microdata, Geospatial data, Other
DATATYPES = ('timeseries', 'microdata', 'geospatial', 'other',)

def get_datatype_items():
    if t.asbool(config.get(FAOCIOK_DATATYPE_FIXED, 'false')):
        dlist = get_vocabulary_items_annotated('datatype')
        for d in DATATYPES:
            for item in dlist:
                if item['value'] == d:
                    yield item
    else:
        for item in get_vocabulary_items_annotated('datatype')[:4]:
            yield item
