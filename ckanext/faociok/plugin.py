import ckan.plugins as plugins
import ckan.plugins.toolkit as t
from ckanext.faociok import schema as s
from ckanext.faociok import helpers as h
from ckanext.faociok import validators as v


class FaociokPlugin(plugins.SingletonPlugin, t.DefaultDatasetForm):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IDatasetForm)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IFacets)

    # IConfigurer

    def update_config(self, config_):
        t.add_template_directory(config_, 'templates')
        t.add_public_directory(config_, 'public')
        t.add_resource('fanstatic', 'faociok')

    # IDatasetForm

    def is_fallback(self):
        # Return True to register this plugin as the default handler for
        # package types not handled by any other IDatasetForm plugin.
        return True
        
    def package_types(self):
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        return []

    def create_package_schema(self):
        schema = super(FaociokPlugin, self).create_package_schema()
        schema.update(s.get_create_package_schema())
        schema['fao_datatype'] += [t.get_converter('convert_to_extras')]
        return schema

    def update_package_schema(self):
        schema = super(FaociokPlugin, self).update_package_schema()
        schema.update(s.get_update_package_schema())
        schema['fao_datatype'] += [t.get_converter('convert_to_extras')]

        return schema

    def show_package_schema(self):
        schema = super(FaociokPlugin, self).show_package_schema()
        schema.update(s.get_show_package_schema())
        field = schema['fao_datatype']
        schema['fao_datatype']  = [t.get_converter('convert_from_extras')] + field
        return schema

    # IValidators

    def get_validators(self):
        return {
            'fao_datatype': v.fao_datatype,
        }

    # ITemplateHelpers

    def get_helpers(self):
        return {
            'get_faociok_vocabulary_items': h.get_vocabulary_items,
            'get_faociok_package_schema': s._get_package_schema,
            'get_fao_datatype': h.get_fao_datatype,
        }

    # IFacets
    def dataset_facets(self, facets_dict, package_type):
        facets_dict['fao_datatype'] = t._("Data type")
        return facets_dict
