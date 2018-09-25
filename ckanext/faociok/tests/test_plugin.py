"""Tests for plugin.py."""
import ckanext.faociok.plugin as plugin
from ckan.plugins import toolkit as t

def test_plugin():
    pass


def test_autocomplete():
    autocomplete = t.get_action('fao_autocomplete')
    ctx = {'ignore_auth': True,
           }

    data = {'q': 'oth', 'vocabulary': 'datatype'}
    autocomplete(ctx, data}

