#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import urllib

from ckan import model
from ckan.plugins import toolkit
from ckan.lib.i18n import get_lang
from ckan.logic import get_action
from ckan.common import request, response, c

from ckan.controllers.api import ApiController


class FaoAutocompleteController(ApiController):

    def fao_autocomplete(self, _vocabulary):
        q = request.str_params.get('incomplete', '')
        q = unicode(urllib.unquote(q), 'utf-8')
        limit = request.params.get('limit', 10)
        lang = request.params.get('lang') or get_lang()
        tag_names = []
        if q:
            context = {'model': model, 'session': model.Session,
                       'user': c.user or c.author, 'auth_user_obj': c.userobj}

            data_dict = {'q': q,
                         'limit': limit,
                         'lang': lang,
                         'vocabulary': _vocabulary}

            tag_names = get_action('fao_autocomplete')(context, data_dict)
            tag_names = tag_names['tags']
        resultSet = {
            'ResultSet': {
                'Result': tag_names,
                },
            'Query': q,
            'Lang': lang,
        }
        return self._finish_ok(resultSet)
