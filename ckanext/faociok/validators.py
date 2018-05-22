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
    if not value:
        return
    value = _deserialize_from_array(value)
    validated = []
    try:
        v = Vocabulary.get(Vocabulary.VOCABULARY_M49_REGIONS)
        for term in value:
            if not v.valid_term(term):
                raise ValueError(_("Term not valid: {}").format(term))
            validated.append(term)
    except Exception, err:
        raise Invalid(_("Invalid m49 regions: {} {}").format(value, err))
    return validated

def _serialize_to_array(value):
    if not isinstance(value, (list, tuple, set,)):
        value = [value]
    serialized = ','.join('{}'.format(v) for v in value)
    return '{{{}}}'.format(serialized)

def _deserialize_from_array(value):

    if not value:
        return 
    if not isinstance(value, list):
        try:
            value = json.loads(value)
        except (ValueError, TypeError,), err:
            pass
    if isinstance(value, list):
        pass
    # handle {,} notation
    elif isinstance(value, (str, unicode,)):
        if value.startswith('{') and value.endswith('}'):
            value = value[1:-1].split(',')
        elif isinstance(value, (str, unicode,)) and value.isdigit():
            value = [value]
        else:
            raise Invalid(_("Invalid m49 regions string value: {}").format(value))
    # single value from form, not encoded
    elif isinstance(value, int):
        value = [str(value)]
    # everything else is ignored
    else:
        raise Invalid(_("Invalid m49 regions value: {}").format(value))
    return value
