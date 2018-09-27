#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for plugin.py."""
import os

from ckan.lib.base import config
from ckan.plugins import toolkit as t
from ckan import model
from ckan.logic import ValidationError

from ckan.tests.helpers import change_config, FunctionalTestBase
from ckanext.faociok.validators import CONFIG_FAO_DATATYPE
from ckanext.faociok.commands.vocabulary import VocabularyCommands
from ckanext.faociok.tests import FaoBaseTestCase, _run_validator_checks, _load_vocabulary, _get_path
from ckanext.faociok.models import Vocabulary, VocabularyTerm, VocabularyLabel


# + regular vocabulary import
# + m49 import 
# + agrovoc import
# + agrovoc autocomplete action
# agrovoc autocomplete view
# other autocomplete
# validators

# ddi harvester (import phase)
# ckan harvester with fao fields


class ValidatorsTestCase(FaoBaseTestCase):

    def test_datatype_validator_no_default(self):
        """
        tests fao_datatype validator without default value in config

        """
        _load_vocabulary('datatype', 'faociok.datatype.csv')

        test_values = ((None, False, None,),
                       ([], False, None,),
                       ("", False, None,),
                       ('invalid', False, None,),
                       ('microdata', True, 'microdata'),
                       )
        _run_validator_checks(test_values, t.get_validator('fao_datatype'))

    @change_config(CONFIG_FAO_DATATYPE, 'default_val')
    def test_datatype_validator_default(self):
        """
        tests fao_datatype validator with default value in config
        """
        _load_vocabulary('datatype', 'faociok.datatype.csv')
        test_values = ((None, True, 'default_val',),
                       ([], True, 'default_val',),
                       ("", True, 'default_val',),
                       ('invalid', False, None,),
                       ('microdata', True, 'microdata'),
                       )
        _run_validator_checks(test_values, t.get_validator('fao_datatype'))

    def test_m49_validator(self):
        """
        Test m49 regions validator
        """
        cli = VocabularyCommands('vocabulary')
        cli.cmd_load('datatype', _get_path('faociok.datatype.csv'))
        cli.cmd_import_m49(_get_path('M49_Codes.xlsx'))

        test_values = (('region', False, None,),
                       ([], True, [],),
                       # oceania, albania
                       ('{9,8}', True, ['9', '8'],),
                       # south america, not in vocabulary
                       ('{5}', False, None,),
                       ('{9,8,5}', False, None,),
                       )
        
        _run_validator_checks(test_values, t.get_validator('fao_m49_regions'))

    def test_agrovoc_validator(self):
        """
        Test Agrovoc validator
        """
        cli = VocabularyCommands('vocabulary')
        cli.cmd_import_agrovoc(_get_path('agrovoc_excerpt.nt'))

        test_values = (('region', False, None,),
                       ([], True, [],),
                       ('{c_100,c_200}', False, None,),
                       ('{c_432,c_7020,c_100}', False, None,),
                       ('{c_432,c_7020}', True, ['c_432', 'c_7020'],),
                       )
        
        _run_validator_checks(test_values, t.get_validator('fao_agrovoc'))

class CommandTestCase(FaoBaseTestCase):

    def test_vocabulary_create(self):
        """
        Test vocabulary command items
        """
        cli = VocabularyCommands('vocabulary')
        cli.cmd_create('test')
        resp = Vocabulary.get('test')
        self.assertIsNotNone(resp)
        self.assertEqual(resp.name, 'test')
        cli.cmd_list()
        usage = cli.usage
        self.assertIsNotNone(usage)

class AutocompleteTestCase(FaoBaseTestCase):

    def test_autocomplete(self):
        """
        Basic autocomplete action test
        """
        _load_vocabulary('datatype', 'faociok.datatype.csv')
        autocomplete = t.get_action('fao_autocomplete')
        ctx = {'mode': model}
        data = {'q': 'oth',
                'lang': 'en',
                'offset': 0,
                'limit': 10,
                'vocabulary': 'datatype'}
        out = autocomplete(ctx, data)
        self.assertEqual(len(out['tags']), 1)
        self.assertEqual(out['tags'][0]['term'], 'other')

        data = {'q': 'oth',
                'lang': 'en',
                'offset': 10,
                'limit': 10,
                'vocabulary': 'datatype'}
        out = autocomplete(ctx, data)
        self.assertEqual(len(out['tags']), 0)


        data = {}
        self.assertRaises(ValidationError, autocomplete, ctx, data)


class AutocompleteControllerTestCase(FunctionalTestBase, FaoBaseTestCase):

    def test_autocomplete_view(self):
        cli = VocabularyCommands('vocabulary')
        cli.cmd_load('datatype', _get_path('faociok.datatype.csv'))
        cli.cmd_import_m49(_get_path('M49_Codes.xlsx'))
        # hack on stacked db session. cli will import data to one db session
        # webapp view may use different session/transaction to retrive it
        # so we make sure session is commited
        model.Session.commit()
        expected_id = '380'

        app = self._get_test_app()
        resp = app.get('/api/util/fao/autocomplete/m49_regions?incomplete=ita&lang=en')

        found_it = False
        for result in resp.json['ResultSet']['Result']:

            if result['term'] == expected_id:
                found_it = result
                break

        self.assertTrue(isinstance(found_it, dict), resp.json)
        self.assertEqual(found_it['label'], 'Italy', found_it)

        resp = app.get('/api/util/fao/autocomplete/m49_regions?incomplete=ita&lang=fr')
        self.assertTrue(len(resp.json['ResultSet']['Result'])> 0, resp.json)
        found_it = False
        for result in resp.json['ResultSet']['Result']:
            if result['term'] == expected_id:
                found_it = result
                break

        self.assertTrue(isinstance(found_it, dict), resp.json)
        self.assertTrue(found_it['label'].endswith(' [FR]'))
