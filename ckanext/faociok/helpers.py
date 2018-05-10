#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ckan.lib.i18n import get_lang
from ckanext.faociok.models import VocabularyTerm


def get_vocabulary_items(vocabulary_name):
    return [{'value': i[0], 'text': i[1]} for i in VocabularyTerm.get_terms(vocabulary_name, lang=get_lang())]
    
