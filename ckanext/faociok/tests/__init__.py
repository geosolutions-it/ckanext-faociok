#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for plugin.py."""
import os
import inspect
import unittest

from ckan.plugins.toolkit import Invalid
from ckan.model.meta import Session
from ckan.plugins import toolkit as t
try:
    from ckan.tests import helpers
except ImportError:
    from ckan.new_tests import helpers

from ckanext.faociok.models import load_vocabulary, setup_models

def _load_vocabulary(vname, fname):
    fpath = _get_path(fname)
    with open(fpath, 'r') as f:
        load_vocabulary(vname, f)

def _get_path(fname):
    this_dir = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(this_dir, '..', '..', '..', 'files', fname)


# wrapper around various validator signatures
def _call_validator(validator, value):
    context = {}
    key = 'key'
    converted_data = {key: value}
    errors = {key: []}

    try:
        validator(key, converted_data, errors, context)
        if errors[key]:
            raise Invalid(errors[key])
        return converted_data[key]

    except TypeError, e:
        # hack to make sure the type error was caused by the wrong
        # number of arguments given.
        if validator.__name__ not in str(e):
            raise
    return validator(converted_data.get(key), context)


def _run_validator_checks(test_values, validator):
    for test_val, is_valid, expected_val in test_values:
        passed = False
        err = None
        try:
            
            value = _call_validator(validator, test_val)
            passed = True
            assert value == expected_val, 'failed return value got {}, expected {}'.format(value, expected_val)
        except t.Invalid, err:
            value = object()
            pass
        assert passed == is_valid, 'failed for {}: {} (return value: {})'.format(test_val, err or 'expected error, but got no validation error', value)


class FaoBaseTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        setup_models()

    def setUp(self):
        helpers.reset_db()

    def tearDown(self):
        Session.rollback()
        

