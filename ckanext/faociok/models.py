#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import json
import csv

from ckan.common import _, ungettext
from sqlalchemy import types, Column, ForeignKey, Index, Table
from sqlalchemy import orm, and_, or_
from sqlalchemy.exc import SQLAlchemyError as SAError
from sqlalchemy.ext.declarative import declarative_base, declared_attr

from ckan.lib.base import config
from ckan.model import Session, Tag, Vocabulary
from ckan.model import meta, repo


log = logging.getLogger(__name__)


DeclarativeBase = declarative_base(metadata=meta.metadata)


class Vocabulary(DeclarativeBase):
    VOCABULARY_DATATYPE = 'datatype'
    VOCABULARY_M49_REGIONS = 'm49_regions'

    __tablename__ = 'faociok_vocabulary'
    id = Column(types.Integer, primary_key=True)
    name = Column(types.Unicode, unique=True)
    has_relations = Column(types.Boolean, default=False)
    
    terms = orm.relationship('VocabularyTerm')

    def __init__(self, name, has_relations=False):
        self.name = name
        self.has_relations = has_relations

    def __str__(self):
        return 'Vocabulary({}{})'.format(self.name, 
                                          ' with relations' if self.has_relations else '')

    def valid_term(self, term):
        q = Session.query(VocabularyTerm).filter(VocabularyTerm.name==term)
        return Session.query(q.exists())

    @classmethod
    def create(cls, name, has_relations=False):
        inst = cls(name=name, has_relations=has_relations)
        Session.add(inst)
        Session.flush()
        return inst

    @classmethod
    def get(cls, name):
        inst = Session.query(cls).filter_by(name=name).first()
        if not inst:
            raise ValueError(_("Vocabulary {} doesn't exist").format(name))
        return inst

    def clear(self):
        q = Session.query(VocabularyLabel)\
                   .join(VocabularyTerm)\
                   .filter(VocabularyTerm.vocabulary_id==self.id)

        for vl in q:
            Session.delete(vl)

        q = Session.query(VocabularyTerm)\
                   .filter(VocabularyTerm.vocabulary_id==self.id)

        for vl in q:
            Session.delete(vl)
        Session.flush()


    @classmethod
    def get_all(cls):
        q = Session.query(cls).all()
        return q

class VocabularyTerm(DeclarativeBase):
    __tablename__ = 'faociok_vocabulary_term'
    id = Column(types.Integer, primary_key=True)
    vocabulary_id = Column(types.Integer, ForeignKey(Vocabulary.id), nullable=False)
    parent_id = Column(types.Integer, ForeignKey('faociok_vocabulary_term.id'), nullable=True)
    name = Column(types.Unicode, nullable=False, unique=True)
    # keep per-term custom properties
    _properties = Column(types.Unicode, nullable=True)

    parent = orm.relationship('VocabularyTerm')
    children = orm.relationship('VocabularyTerm')
    labels = orm.relationship('VocabularyLabel')

    @property
    def properties(self):
        return json.loads(self._properties or '{}')

    @properties.setter
    def properties(self, value):
        self._properties = json.dumps(value)

    def __init__(self, vocabulary, name, parent=None, properties=None):
        if isinstance(vocabulary, Vocabulary):
            self.vocabulary_id = vocabulary.id
        else:
            self.vocabulary_id = vocabulary
        self.name = name
        if parent:
            self.parent_id = parent.id
        if properties is not None:
            self.properties = properties

    def set_labels(self, labels):
        for k, v in labels.items():
            VocabularyLabel.create(self, lang=k, label=v)

    def get_label(self, lang):
        return Session.query(VocabularyLabel).filter(VocabularyLabel.term_id==self.id,
                                                     VocabularyLabel.lang==lang).first()
    
    @classmethod
    def get(cls, vocab, name):
        if isinstance(vocab, Vocabulary):
            item = Session.query(cls).filter(cls.vocabulary_id==vocab.id,
                                             cls.name==name)\
                                     .first()

        else:
            item = Session.query(cls).join(Vocabulary)\
                                     .filter(Vocabulary.name==vocab, cls.name==name).first()

        if not item:
            raise ValueError(_("No term {} for vocabulary {}").format(name, vocab))
        return item

    @classmethod
    def create(cls, vocab, name, labels=None, parent=None, properties=None):
        if not isinstance(vocab, Vocabulary):
            vocab = Vocabulary.get(vocab)
        inst = cls(vocab, name, parent, properties)
        Session.add(inst)
        Session.flush()
        if labels:
            inst.set_labels(labels)
        return inst

    @classmethod
    def get_terms_q(cls, vocabulary_name, lang):
        s = Session
        q = s.query(cls.name, VocabularyLabel.label).join(Vocabulary)\
                                                    .outerjoin(VocabularyLabel)\
                                                    .filter(Vocabulary.name==vocabulary_name,
                                                            VocabularyLabel.lang==lang)
        return q
    
    @classmethod
    def get_terms(cls, vocabulary_name, lang):
        q = cls.get_terms_q(vocabulary_name, lang)
        return [(item[0], item[1] or item[0],) for item in q]


class VocabularyLabel(DeclarativeBase):
    __tablename__ = 'faociok_vocabulary_label'
    id = Column(types.Integer, primary_key=True)
    term_id = Column(types.Integer, ForeignKey(VocabularyTerm.id))
    label = Column(types.Unicode, nullable=False)
    lang = Column(types.Unicode, nullable=False)
    term = orm.relationship(VocabularyTerm)

    def __init__(self, term, label, lang):
        self.term = term
        self.label = label
        self.lang = lang

    @classmethod
    def create(cls, term, label, lang):
        inst = cls(term, label, lang)
        Session.add(inst)
        Session.flush()
        return inst


def setup_models():
    for t in (Vocabulary.__table__,
              VocabularyTerm.__table__,
              VocabularyLabel.__table__):
        if not t.exists():
            t.create()

def load_vocabulary(vocabulary_name, fh, **vocab_config):
    """
    Load Vocabulary terms and lang values

    fh is a file-like object containing csv data in format:
     * first row contains header with values
       * term, $languagecode,...
       or 
       * parent, term, $languagecode..
     * each next row contains values:
       
     For example:

        term,en,it,de,fr
        microdata,Microdata,,,
        geospatial-data,Geospatial data,,,

     or:


        parent,term,en,it,de,fr
        ,microdata,Microdata,,,
        microdata,geospatial-data,Geospatial data,,,

    @param vocabulary_name Vocabulary instance or name of vocabulary
    @param file-like object with terms data

    @rtype int number of terms loaded
    """
    try:
        vocab = Vocabulary.get(vocabulary_name)
        vocab.clear()
    except ValueError:
        vocab = Vocabulary.create(vocabulary_name, **vocab_config)
    
    
    r = csv.reader(fh)
    counter = 0
    # first row is a header
    header = list(r.next())

    # row offset for data, default 1, as column 0 has term.name
    row_offset = 1
    # get headers with lang names
    headers = header[row_offset:]
    parent_idx = None
    default = 0

    # establish if we have a parent
    if header[0] == 'parent':
        if not vocab.has_relations:
            raise ValueError(_("Cannot use 'parent' colum if "
                               "vocabulary that doesn't "
                               "support relations"))
        row_offset = 2
        default = 1
        headers = header[row_offset:]
        parent_idx = 0
    
    for row in r:
        # all data for row
        _data = dict(zip(headers, row[row_offset:]))
        # properties are cells for which header starts with 'property:' prefix
        properties = dict( (k[len('property:'):],v,) for k,v in _data.items() if k.startswith('property:'))
        # labels are cells for which header starts with 'lang:'
        labels = dict( (k,v,) for k,v in _data.items() if k.startswith('lang:'))

        if not labels:
            continue
        parent = None
        default_label = row[default]
        try:
            existing = VocabularyTerm.get(vocab, default_label)
            continue
        except ValueError:
            pass
        if parent_idx is not None:
            parent_name = row[parent_idx] 
            if parent_name:
                parent = VocabularyTerm.get(vocab, parent_name)
        VocabularyTerm.create(vocab, default_label, labels, parent=parent, properties=properties)
        counter += 1
    return counter
