#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from ckan.lib.base import _, ungettext, config
from ckan.plugins.toolkit import Invalid
from ckanext.faociok.models import Vocabulary
from ckan.lib.navl.dictization_functions import Missing

CONFIG_FAO_DATATYPE = 'ckanext.faociok.datatype'


def fao_datatype(value, context):
    DEFAULT_DATATYPE = config.get(CONFIG_FAO_DATATYPE)
    if not value and DEFAULT_DATATYPE:
        return DEFAULT_DATATYPE
    try:
        v = Vocabulary.get(Vocabulary.VOCABULARY_DATATYPE)
        if not v.valid_term(value):
            raise ValueError(_("Term not valid"))
        return value
    except Exception, err:
        raise Invalid(_("Invalid datatype value: {}: {}").format(value, err))

def fao_agrovoc(key, flattened_data, errors, context):
    # we use extended api to update data dict in-place
    # this way we avoid various errors in harvesters,
    # which don't populate extras properly
    value = flattened_data[key]
    if isinstance(value, Missing) or value is None:
        flattened_data[key] = []
    else:
        value = _deserialize_from_array(value)
        validated = []
        try:
            v = Vocabulary.get(Vocabulary.VOCABULARY_AGROVOC)
            for term in value:
                if not v.valid_term(term):
                    errors[key].append(ValueError(_("Term not valid: {}").format(term)))
                    break
                validated.append(term)
            flattened_data[key] = validated
        except Exception, err:
            errors[key].append(Invalid(_("Invalid AGROVOC term: {} {}").format(value, err)))

def fao_m49_regions(key, flattened_data, errors, context):
    # we use extended api to update data dict in-place
    # this way we avoid various errors in harvesters,
    # which don't populate extras properly
    value = flattened_data[key]
    if isinstance(value, Missing) or value is None:
        flattened_data[key] = []
    else:
        value = _deserialize_from_array(value)
        validated = []
        try:
            v = Vocabulary.get(Vocabulary.VOCABULARY_M49_REGIONS)
            for term in value:
                if not v.valid_term(term):
                    errors[key].append(ValueError(_("Term not valid: {}").format(term)))
                    break
                validated.append(term)
            flattened_data[key] = validated
        except Exception, err:
            errors[key].append(Invalid(_("Invalid m49 regions: {} {}").format(value, err)))

def _serialize_to_array(value):
    if isinstance(value, (str, unicode,)) and value.startswith('{') and value.endswith('}'):
        return value
    if not isinstance(value, (list, tuple, set,)):
        value = [value]
    serialized = ','.join('{}'.format(v) for v in value)
    return '{{{}}}'.format(serialized)

def _deserialize_from_array(value):
    if not value:
        return []
    # shorthand for empty array
    elif value == '{}' or value == '':
        return []
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
            if not value[1:-1]:
                value = []
            else:
                value = value[1:-1].split(',')
        elif isinstance(value, (str, unicode,)) and value.isdigit():
            value = [value]
        else:
            value = value.split(',')
    # single value from form, not encoded
    elif isinstance(value, int):
        value = [str(value)]
    # everything else is ignored
    else:
        raise Invalid(_("Invalid list of values: {}").format(value))
    return value
