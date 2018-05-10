#!/usr/bin/env python
# -*- coding: utf-8 -*-


from ckan.common import _, ungettext
from ckan.plugins import PluginImplementations
from ckanext.faociok.models import Vocabulary


def _get_package_schema():
    return [
        {'name': 'datatype',
         'validator': ['fao_datatype'],
         'element': 'select',
         'label': _("Data type"),
         'vocabulary_name': Vocabulary.VOCABULARY_DATATYPE,
         'description': _("Select data type of dataset"),
         'is_required': True,
         },
    ]

def get_create_package_schema():
    return _get_package_schema()


def get_update_package_schema():
    return _get_package_schema()
