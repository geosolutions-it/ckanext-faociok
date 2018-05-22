#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ckan.plugins.toolkit as toolkit

import json
from ckan.lib.i18n import get_lang
import ckan.logic as logic
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

def get_vocabulary_items(vocabulary_name):
    return VocabularyTerm.get_terms(vocabulary_name, lang=get_lang())
    
def load_json(value, fail=False):
    try:
        return json.loads(value)
    except (ValueError, TypeError,):
        if fail:
            raise
        return value

def get_vocabulary_items_annotated(vocabulary_name):
    return VocabularyTerm.get_terms(vocabulary_name, lang=get_lang(), include_dataset_count=True)

def fao_get_action(action_name, data_dict=None):
    '''BAD BAD WORKAROUND'''
    if data_dict is None:
        data_dict = {}
    return logic.get_action(action_name)({}, data_dict)

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
