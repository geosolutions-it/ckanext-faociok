#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from ckan.lib.i18n import get_lang
from ckanext.faociok.models import Vocabulary, VocabularyTerm



def get_fao_datatype(name):
    lang = get_lang()
    term = VocabularyTerm.get(Vocabulary.VOCABULARY_DATATYPE, name)
    return term.get_label(lang).label or term.name

def get_fao_m49_region(name):
    lang = get_lang()
    term = VocabularyTerm.get(Vocabulary.VOCABULARY_M49_REGIONS, name)
    return term.get_label(lang).label or term.get_label('en').label
    

def format_term(term, depth):
    return u'{}{}{}'.format('-' * depth, ' ' if depth else '', term)

def get_vocabulary_items(vocabulary_name, in_list=False):
    return VocabularyTerm.get_terms(vocabulary_name, lang=get_lang(), in_list=in_list)
    
def load_json(value):
    val = json.loads(value)
    return val

def get_vocabulary_items_annotated(vocabulary_name, in_list=False):
    return VocabularyTerm.get_terms(vocabulary_name, lang=get_lang(), include_dataset_count=True, in_list=in_list)
