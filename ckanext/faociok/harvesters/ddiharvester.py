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

        content = harvest_object.content
        if isinstance(content, unicode):
            content = content.encode('utf-8')
        _pkg_dict = ckan_metadata.load(content)
        
        region_name = _pkg_dict['country']
        region = VocabularyTerm.get_term(Vocabulary.VOCABULARY_M49_REGIONS, region_name).scalar()
        extras = ret.get('extras') or []
        
        found_in_extras = -1
        for idx, ex in enumerate(extras):
            if ex['key'] == 'fao_datatype':
                found_in_extras = idx
                break
        if found_in_extras > -1:
            extras.pop(found_in_extras)

        if region:
            found_in_extras = -1
            for ex in extras:
                if ex['key'] == 'fao_m49_regions':
                    found_in_extras = idx
                    break
            if found_in_extras > -1:
                extras.pop(found_in_extras)
        ret['fao_m49_regions'] = '{{{}}}'.format(region.name)
        ret['fao_datatype'] = 'microdata'
        ret['metadata_modified'] = None

        out = pupd(self._get_context(), ret)
        
        return ret


