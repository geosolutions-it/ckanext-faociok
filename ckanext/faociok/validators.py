#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ckan.common import _, ungettext
from ckan.plugins.toolkit import Invalid
from ckanext.faociok.models import Vocabulary

def fao_datatype(value, context):
    try:
        v = Vocabulary.get(Vocabulary.VOCABULARY_DATATYPE)
        if not v.valid_term(value):
            raise ValueError(_("Term not valid"))
    except Exception, err:
        raise Invalid(_("Invalid datatype value: {}: {}").format(value, err))
    
    return value
