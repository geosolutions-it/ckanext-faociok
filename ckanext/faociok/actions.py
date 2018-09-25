#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import and_, or_
from ckan.logic import get_or_bust
from ckanext.faociok.models import VocabularyTerm, Vocabulary, VocabularyLabel

def fao_autocomplete(context, data_dict):
    model = context['model']

    term = (data_dict.get('query') or data_dict.get('q') or '').strip()
    vocabulary_name = get_or_bust(data_dict, 'vocabulary')
    lang = get_or_bust(data_dict, 'lang')
    offset = data_dict.get('offset')
    limit = data_dict.get('limit')

    q = model.Session.query(VocabularyLabel.label, VocabularyTerm.name)\
                     .join(VocabularyTerm,
                           VocabularyTerm.id == VocabularyLabel.term_id)\
                     .join(Vocabulary,
                           Vocabulary.id == VocabularyTerm.vocabulary_id)\
                     .filter(Vocabulary.name == vocabulary_name)

    q = q.distinct()\
         .filter(or_(VocabularyTerm.name == term,
                     and_(VocabularyLabel.label.ilike('%{}%'.format(term)),
                          VocabularyLabel.lang == lang)))\
         .order_by(VocabularyTerm.name, VocabularyLabel.label)

    q = q.offset(offset)
    q = q.limit(limit)
    count = q.count()
    return {'tags': [{'name': t.name, 'term': t.name, 'label': t.label} for t in q.all()],
            'count':  count,
            'lang': lang}
