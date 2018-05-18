#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import json
import csv

from ckan.common import _, ungettext
from sqlalchemy import types, Column, ForeignKey, Index, Table
from sqlalchemy import orm, and_, or_, desc
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
    
    terms = orm.relationship('VocabularyTerm', back_populates='vocabulary')

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
    depth = Column(types.Integer, nullable=False, default=0)
    path = Column(types.Unicode, nullable=False, default=u'')
    # keep per-term custom properties
    _properties = Column(types.Unicode, nullable=True)

    vocabulary = orm.relationship('Vocabulary', uselist=False, back_populates='terms')
    labels = orm.relationship('VocabularyLabel', back_populates='term')
    parent = orm.relationship('VocabularyTerm', lazy=True, uselist=False, remote_side=[id])

    @property
    def properties(self):
        return json.loads(self._properties or '{}')

    @properties.setter
    def properties(self, value):
        self._properties = json.dumps(value)

    def set_labels(self, labels):
        for k, v in labels.items():
            VocabularyLabel.create(self, lang=k, label=v)

    def get_label(self, lang):
        return Session.query(VocabularyLabel).filter(VocabularyLabel.term_id==self.id,
                                                     VocabularyLabel.lang==lang).first()
    def get_path(self):
        parent = self
        old_parent = None
        out = []

        while parent and parent != old_parent:
            out.append(parent.name)
            old_parent = parent
            parent = parent.parent
        return '/'.join(reversed(out))

    def update_path(self):
        path = self.get_path()
        self.path = path

    @classmethod
    def get(cls, vocab, name):
        if isinstance(vocab, Vocabulary):
            item = Session.query(cls).filter(cls.vocabulary_id==vocab.id,
                                             cls.name==name).first()

        else:
            item = Session.query(cls).join(Vocabulary)\
                                     .filter(Vocabulary.name==vocab, cls.name==name).first()

        if not item:
            log.info(_("No term {} for vocabulary {}").format(name, vocab))

        return item

    @classmethod
    def create(cls, vocab, name, labels=None, parent=None, properties=None):
        if not isinstance(vocab, Vocabulary):
            vocab = Vocabulary.get(vocab)
        
        inst = cls(vocabulary=vocab,
                   name=name,
                   depth=parent.depth +1 if parent else 0,
                   parent=parent)
        inst.properties = properties or {}
        if labels:
            inst.set_labels(labels)

        inst.update_path()
        Session.add(inst)
        Session.flush()
        return inst

    @classmethod
    def get_terms_q(cls, vocabulary_name, lang):
        s = Session
        q = s.query(cls.name, VocabularyLabel.label, cls.depth, cls.id).join(Vocabulary)\
                                                    .outerjoin(VocabularyLabel)\
                                                    .filter(Vocabulary.name==vocabulary_name,
                                                            VocabularyLabel.lang==lang)\
                                                    .order_by(cls.path)
        return q
    
    @classmethod
    def get_terms(cls, vocabulary_name, lang):
        q = cls.get_terms_q(vocabulary_name, lang)
        return [(item[0], item[1] or item[0], item[2], item[3],) for item in q]


class VocabularyLabel(DeclarativeBase):
    __tablename__ = 'faociok_vocabulary_label'
    id = Column(types.Integer, primary_key=True)
    term_id = Column(types.Integer, ForeignKey(VocabularyTerm.id))
    label = Column(types.Unicode, nullable=False)
    lang = Column(types.Unicode, nullable=False)
    term = orm.relationship(VocabularyTerm, uselist=False, back_populates='labels')

    @classmethod
    def create(cls, term, label, lang):
        inst = cls(term=term,
                   label=label,
                   lang=lang)
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
       * term (required)
       * parent (optional)
       * lang:LANGCODE (optional)
       * property:PROPNAME (optional)
     * each next row contains values:
       
     For example:

        parent, term, property:ISO3, lang:en, lang:it, lang:de, lang:fr
              ,EU   ,              , Europe , Europa,,
        EU    ,031  , ITA          , Italy  , Italia,,

     or:
        term,lang:en,lang:it
        microdata,Microdata, Microdata
        geospatial,Geospatial data,Dati Geospaziali

    @param vocabulary_name Vocabulary instance or name of vocabulary
    @param file-like object with terms data

    @rtype int number of terms loaded
    """
    
    try:
        vocab = Vocabulary.get(vocabulary_name)
        vocab.clear()
    except ValueError:
        vocab = Vocabulary.create(vocabulary_name, **vocab_config)
    

    print(_("Using Vocabulary{}").format(vocab))

    rows = csv.reader(fh)
    counter = 0
    # first row is a header
    headers = list(rows.next())

    parent_idx = None
    term_idx = None

    idx = 0   
    for header in headers:
        if header == "parent":
            print(_("Parent column found at idx {}").format(idx))
            parent_idx = idx
        elif header == "term":
            print(_("Term column found at idx {}").format(idx))
            term_idx = idx
        elif not header.startswith('lang:') and not header.startswith('property:'):
            print(_("Column {} will not be stored").format(header))
        idx = idx + 1

    # establish if we have a parent
    if parent_idx is not None and not vocab.has_relations:
        raise ValueError(_("Cannot use 'parent' colum if "
                           "vocabulary that doesn't support relations"))

    if term_idx is None:
        raise ValueError(_("Term column not found"))
    
    for row in rows:
        # all data for row
        _data = dict(zip(headers, row))
        # properties are cells for which header starts with 'property:' prefix
        properties = dict( (k[len('property:'):],v,) for k,v in _data.items() if k.startswith('property:') and v)
        # labels are cells for which header starts with 'lang:'
        labels = dict( (k[len('lang:'):],v,) for k,v in _data.items() if k.startswith('lang:'))

        term = row[term_idx]
        parent = row[parent_idx] if parent_idx is not None else None

        if not term:
            print(_("Skipping row with no term: {}").format(_data))
            continue

        term_from_db = VocabularyTerm.get(vocab, term)
        # print(_("TERM FROM DB ID[{}] DB[{}] ").format(term, term_from_db))
        if term_from_db:
            print(_("Skipping existing term: INPUT [{}] DB [{}] ").format(_data, term_from_db))
            continue

        parent_from_db = VocabularyTerm.get(vocab, parent) if parent else None
        # print(_("Term [{}] has PARENT [{}] [{}] ").format(term, parent, parent_from_db))
        
        VocabularyTerm.create(vocab, term, labels, parent=parent_from_db, properties=properties)
        if not VocabularyTerm.get(vocab, term):
            print(_("ERROR: TERM NOT CREATED  vocab[{}] term[{}] data[{}]").format(vocab, term, _data))
        
        
        counter += 1
    return counter
