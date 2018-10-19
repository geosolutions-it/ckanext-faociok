#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ckan.plugins import toolkit as t

def _get_user():
    user = t.get_action('get_site_user')(
        {'ignore_auth': True, 'defer_commit': True},
        {})
    return user

