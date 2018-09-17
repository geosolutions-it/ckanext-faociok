#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

from ckan import model
from ckan.plugins import toolkit
from ckan.lib.i18n import get_lang

from ckan.controllers.api import ApiController


class FaoAutocompleteController(ApiController):

    def fao_autocomplete(self, _vocabulary):
        q = request.str_params.get('incomplete', '')
        q = unicode(urllib.unquote(q), 'utf-8')
        limit = request.params.get('limit', 10)
        tag_names = []
        if q:
            context = {'model': model, 'session': model.Session,
                       'user': c.user or c.author, 'auth_user_obj': c.userobj}

            data_dict = {'q': q,
                         'limit': limit,
                         'lang': h.get_lang(),
                         'vocabulary': _vocabulary)

            tag_names = get_action('fao_autocomplete')(context, data_dict)

        resultSet = {
            'ResultSet': {
                'Result': [{'Name': tag} for tag in tag_names['tags']]
            }
        }
        return self._finish_ok(resultSet)
