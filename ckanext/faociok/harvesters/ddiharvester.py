# -*- coding: utf-8 -*-

from ckan import model
from ckan.model import Session
from ckan.plugins import toolkit

from ckanext.faociok.models import VocabularyTerm, Vocabulary
from ckanext.faociok.plugin import FaociokPlugin

from ckanext.ddi.harvesters.ddiharvester import NadaHarvester
from ckanext.ddi.importer import DdiCkanMetadata


class FaoNadaHarvester(NadaHarvester):

    def info(self):
        return {
            'name': 'fao-nada',
            'title': 'FAO/NADA harvester for DDI',
            'description': (
                'FAO-CIOK Harvests DDI data from a NADA instance '
                '(survey cataloguing software).'
            ),
            'form_config_interface': 'Text'
        }

    def _get_context(self):
        user_name = self._get_user_name()
        # Check API version
        if self.config:
            try:
                api_version = int(self.config.get('api_version', 2))
            except ValueError:
                raise ValueError('api_version must be an integer')
        else:
            api_version = 2

        schema = FaociokPlugin().update_package_schema()
        context = {
                'model': model,
                'session': Session,
                'user': user_name,
                'api_version': api_version,
                'schema': schema,
                'ignore_auth': True,
            }
        return context

    def import_stage(self, harvest_object):
        content = harvest_object.content
        # when xml is unicode and has charset declaration in <?xml.. part
        # this will raise exception in lxml
        # ValueError: Unicode strings with encoding declaration are not supported. 
        #    Please use bytes input or XML fragments without declaration.
        # that's why we encode to str
        if isinstance(content, unicode):
            try:
                content = content.encode('utf-8')
            except UnicodeEncodeError:
                pass
        harvest_object.content = content

        ret = super(FaoNadaHarvester, self).import_stage(harvest_object)
        if not ret:
            return ret
        # datatype
        pkg_id = harvest_object.package_id
        context = self._get_context()
        pget = toolkit.get_action('package_show')
        pupd = toolkit.get_action('package_update')

        ret = pget(context, {'name_or_id': pkg_id})

        # get locations/m49
        ckan_metadata = DdiCkanMetadata()

        _pkg_dict = ckan_metadata.load(harvest_object.content)
        
        region_name = _pkg_dict.get('country')
        region = None
        if region_name:
            region = VocabularyTerm.get_term(Vocabulary.VOCABULARY_M49_REGIONS, region_name).first()
            if region:
                region = region[0]
        extras = ret.get('extras') or []

        # microdata don't have any datatype field, so we use predefined one, 'microdata'
        # in case this is changed in ckan, we should preserve this field in updated dataset
        found_in_extras = -1
        for idx, ex in enumerate(extras):
            if ex['key'] == 'fao_datatype':
                found_in_extras = idx
                break
        if found_in_extras > -1:
            orig_datatype = extras[found_in_extras]
            # might be Missing instance
            if isinstance(orig_datatype['value'], (str, unicode,)):
                ret['fao_datatype'] = orig_datatype['value']
            else:
                ret['fao_datatype'] = 'microdata'
        else:
            ret['fao_datatype'] = 'microdata'

        # agrovoc is local, so we need to preserve
        found_in_extras = -1
        for idx, ex in enumerate(extras):
            if ex['key'] == 'fao_agrovoc':
                found_in_extras = idx
                break
        if found_in_extras > -1:
            orig_agrovoc = extras[found_in_extras]
            # might be Missing instance
            if isinstance(orig_datatype['value'], (str, unicode,)):
                ret['fao_agrovoc'] = orig_agrovoc['value']
            else:
                ret['fao_agrovoc'] = '{}'
        else:
            ret['fao_agrovoc'] = '{}'
        
        # remove duplicated extras
        ret['extras'] = [ex for ex in extras if not ex['key'].startswith('fao_')]

        ret['fao_m49_regions'] = '{{{}}}'.format(region.name) if region else '{}'
        ret['metadata_modified'] = None
        out = pupd(self._get_context(), ret)
        
        return ret
