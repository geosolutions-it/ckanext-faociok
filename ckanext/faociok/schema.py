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
         'is_required': True,
         },
         {'name': 'fao_m49_region',
          'validators': [t.get_validator('fao_m49_region')],
          'element': 'select',
          'label': _("M49 Region"),
          'vocabulary_name': Vocabulary.VOCABULARY_M49_REGION,
          'description': _("Regions according to UN M.49 Standard"),
          'is_required': False},
    ]

def get_create_package_schema():
    return dict( (i['name'], i['validators'],) for i in _get_package_schema())

def get_update_package_schema():
    return dict( (i['name'], i['validators'],) for i in _get_package_schema())

def get_show_package_schema():
    return dict( (i['name'], i['validators'],) for i in _get_package_schema())
