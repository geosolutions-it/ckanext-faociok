#!/usr/bin/env python
# -*- coding: utf-8 -*-


from ckan.common import _, ungettext
import ckan.plugins.toolkit as t
from ckan.plugins import PluginImplementations
from ckanext.faociok.models import Vocabulary


def _get_package_schema():
    return [
        {'name': 'fao_datatype',
         'validators': [t.get_validator('fao_datatype')],
         'element': 'select',
         'label': _("Data type"),
         'vocabulary_name': Vocabulary.VOCABULARY_DATATYPE,
         'description': _("Select data type of dataset"),
         'multiple': False,
         'type': 'raw',
         'additional_module': None,
         'autocomplete': False,
         'is_required': True,
         },
         {'name': 'fao_m49_regions',
          'validators': [t.get_validator('ignore_missing'), t.get_validator('fao_m49_regions')],
          'element': 'select',
          'multiple': True,
          'type': 'json',
          'autocomplete': True,
          'label': _("M49 Regions"),
          'additional_module': 'm49_regions',
          'vocabulary_name': Vocabulary.VOCABULARY_M49_REGIONS,
          'description': _("Regions according to UN M.49 Standard"),
          'is_required': False},
    ]

def get_create_package_schema():
    return dict( (i['name'], i['validators'],) for i in _get_package_schema())

def get_update_package_schema():
    return dict( (i['name'], i['validators'],) for i in _get_package_schema())

def get_show_package_schema():
    return dict( (i['name'], i['validators'],) for i in _get_package_schema())
