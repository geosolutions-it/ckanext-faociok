#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ckanext.faociok.models import VocabularyTerm, Vocabulary, VocabularyLabel
from sqlalchemy import and_


def fao_autocomplete(context, data):
    model = context['model']
    
    term = (data_dict.get('query') or data_dict.get('q') or '').strip()
    lang = _get_or_bust(data_dict, 'lang')
    offset = data_dict.get('offset')
    limit = data_dict.get('limit')
    vocabulary_name = _get_or_bust(data_dict, 'vocabulary')

    # TODO: should we check for user authentication first?
    q = model.Session.query(VocabularyLabel)\
                     .join(VocabularyTerm,
                           VocabularyTerm.id == VocabularyLabel.term_id)\
                     .join(Vocabulary,
                           Vocabulary.id == VocabularyTerm.vocabulary_id)\
                     .filter(Vocabulary.name == vocabulary_name)
            
    q = q.distinct()\
         .filter(and_(VocabularyLabel.label.ilike('%{}%'.format(term)))
                      VocabularyLabel.lang == lang))

    q = q.offset(offset)
    q = q.limit(limit)
    return {'tags': [t.label for t in q.all()],
            'count':  count,
            'lang': lang}
