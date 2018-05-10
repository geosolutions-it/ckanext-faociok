import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckanext.faociok.schema import get_create_package_schema, get_update_package_schema, _get_package_schema
from ckanext.faociok import helpers as h


class FaociokPlugin(plugins.SingletonPlugin, toolkit.DefaultDatasetForm):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IDatasetForm)
    plugins.implements(plugins.ITemplateHelpers)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'faociok')

    def is_fallback(self):
        # Return True to register this plugin as the default handler for
        # package types not handled by any other IDatasetForm plugin.
        return True
        
    def package_types(self):
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        return []

    def create_package_schema(self):
        return get_create_package_schema()

    def update_package_schema(self):
        return get_update_package_schema()


    def get_helpers(self):
        return {
            'get_faociok_vocabulary_items': h.get_vocabulary_items,
            'get_faociok_package_schema': _get_package_schema,

        }
