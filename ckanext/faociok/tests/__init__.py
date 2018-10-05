#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for plugin.py."""
import os
import unittest

from ckan import model
from ckan.plugins.toolkit import Invalid
from ckan.model.meta import Session
from ckan.model import repo
from ckan.plugins import toolkit as t
try:
    from ckan.tests import helpers
except ImportError:
    from ckan.new_tests import helpers

from ckanext.faociok.models import load_vocabulary, setup_models
from ckanext.harvest.model import setup as setup_harvester_models


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
            assert value == expected_val,\
                'failed return value got {}, expected {}'.format(value,
                                                                 expected_val)
        except t.Invalid, err:
            value = object()
            pass
        assert passed == is_valid,\
            'failed for {}: {} (return value: {})'.format(
                test_val,
                err or 'expected error, but got no validation error',
                value)


class FaoBaseTestCase(unittest.TestCase):

    def setUp(self):
        helpers.reset_db()
        setup_models()

    def tearDown(self):
        Session.rollback()


class HarvesterTestCase(FaoBaseTestCase):

    def setUp(self):
        super(HarvesterTestCase, self).setUp()
        print('setting up harvest models')
        setup_harvester_models()

    def _create_harvest_source(self, ctx, mock_url, **kwargs):

        source_dict = {
            'title': 'Test Source',
            'name': 'test-source',
            'url': mock_url,
            'source_type': kwargs.get('source_type') or 'dcat_rdf',
        }
        source_dict.update(**kwargs)
        harvest_source = helpers.call_action('harvest_source_create',
                                             context=ctx, **source_dict)
        return harvest_source

    def _create_harvest_job(self, ctx, harvest_source_id):

        harvest_job = helpers.call_action('harvest_job_create',
                                          context=ctx,
                                          source_id=harvest_source_id)
        return harvest_job

    def _create_harvest_obj(self, mock_url, **kwargs):
        ctx = {'session': Session,
               'model': model}
        s = self._create_harvest_source(ctx, mock_url, **kwargs)
        Session.flush()
        j = self._create_harvest_job(ctx, s['id'])
        Session.flush()
        h = helpers.call_action('harvest_object_create',
                                context=ctx,
                                job_id=j['id'],
                                source_id=s['id'])
        return h
