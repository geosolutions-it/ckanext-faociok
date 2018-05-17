#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
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

def fao_m49_regions(value, context):
    if not isinstance(value, list):
        try:
            value = json.loads(value)
        except (ValueError, TypeError,), err:
            raise Invalid(_("Invalid m49 regions value: {} {}").format(value, err))
    validated = []
    try:
        v = Vocabulary.get(Vocabulary.VOCABULARY_M49_REGIONS)
        for term in value:
            if not v.valid_term(term):
                raise ValueError(_("Term not valid: {}").format(term))
            validated.append(term)
    except Exception, err:
        raise Invalid(_("Invalid m49 regions: {} {}").format(value, err))
    return json.dumps(validated)
