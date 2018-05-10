#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ckanext.dcatapit.interfaces as interfaces

from ckan.common import _, ungettext
from ckan.plugins import PluginImplementations
from ckanext.faociok.models import get_datatypes()


def _get_package_schema():
    return [
        {'name': 'datatype',
         'validator': ['fao_datatype'],
         'element': 'select',
         'values': get_datatypes(),
         'label': _("Data type"),
         'description': _("Select data type of dataset"),
         'is_required': True,
         },
    ]

def get_create_package_schema():
    return _get_package_schema()


def get_update_package_schema():
    return _get_package_schema()
