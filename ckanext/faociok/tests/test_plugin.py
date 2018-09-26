#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for plugin.py."""
import os

from ckan.lib.base import config
from ckan.plugins import toolkit as t
from ckan.tests.helpers import change_config
from ckanext.faociok.validators import CONFIG_FAO_DATATYPE
from ckanext.faociok.commands.vocabulary import VocabularyCommands
from ckanext.faociok.tests import FaoBaseTestCase, _run_validator_checks, _load_vocabulary, _get_path
from ckanext.faociok.models import Vocabulary


# regular vocabulary import
# m49 import 
# agrovoc import
# agrovoc autocomplete
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

    def test_vocabulary_create(self):
        cli = VocabularyCommands('vocabulary')
        cli.cmd_create('test')
        resp = Vocabulary.get('test')
        self.assertIsNotNone(resp)
        self.assertEqual(resp.name, 'test')
        cli.cmd_list()
        usage = cli.usage
        self.assertIsNotNone(usage)


