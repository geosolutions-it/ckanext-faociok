#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from ckan.lib.i18n import get_lang
from ckanext.faociok import validators as v
from ckan.plugins import toolkit as t
from ckan.lib import helpers as h
from ckanext.faociok.models import Vocabulary, VocabularyTerm


def get_fao_datatype(name):
    lang = get_lang()
    term = VocabularyTerm.get(Vocabulary.VOCABULARY_DATATYPE, name)
    return (term.get_label(lang).label or term.name) if term else None


def get_fao_m49_region(name):
    lang = get_lang()
    term = VocabularyTerm.get(Vocabulary.VOCABULARY_M49_REGIONS, name)
    if term:
        return term.get_label(lang).label or term.get_label('en').label
    return name


def format_term(term, depth):
    return u'{}{}{}'.format('-' * depth, ' ' if depth else '', term)


def get_vocabulary_items(vocabulary_name, is_multiple=False, filters=None):
    return VocabularyTerm.get_terms(vocabulary_name,
                                    lang=get_lang(),
                                    is_multiple=is_multiple,
                                    filters=filters)


def load_json(value, fail=False):
    try:
        return json.loads(value)
    except (ValueError, TypeError,):
        if fail:
            raise
        return value


def get_field_data(data, field):
    if field.get('multiple'):
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
