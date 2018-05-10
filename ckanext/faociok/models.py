#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

import csv

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
    __tablename__ = 'faociok_vocabulary'
    id = Column(types.Integer, primary_key=True)
    name = Column(types.Unicode, unique=True)
    has_relations = Column(types.Boolean, default=False)
    
    terms = orm.relationship('VocabularyTerm')

    def __init__(self, name, has_relations=False):
        self.name = name
        self.has_relations = has_relations

    @classmethod
    def create(cls, name, has_relations=False):
        inst = cls(name=name, has_relations=False)
        Session.add(inst)
        Session.flush()
        return inst

    @classmethod
    def get(cls, name):
        inst = Session.query(cls).filter_by(name=name).first()
        if not inst:
            raise ValueError("Vocabulary {} doesn't exist".format(name))
        return inst

    def clear(self):
        self.terms.clear()

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

    parent = orm.relationship('VocabularyTerm')
    children = orm.relationship('VocabularyTerm')
    labels = orm.relationship('VocabularyLabel')

    def __init__(self, vocabulary, name, parent=None):
        if isinstance(vocabulary, Vocabulary):
            self.vocabulary_id = vocabulary.id
        else:
            self.vocabulary_id = vocabulary
        self.name = name
        if parent:
            self.parent = parent

    def set_labels(self, labels):
        for k, v in labels.items():
            VocabularyLabel.create(self, lang=k, label=v)

    
    @classmethod
    def get(cls, vocab, name):
        item = Session.query(cls).filter(vocabulary_id==vocab.id, name==name).first()
        if not item:
            raise ValueError("No term {} for vocabulary {}".format(name, vocab))
        return item

    @classmethod
    def create(cls, vocab, name, labels=None, parent=None):
        if not isinstance(vocab, Vocabulary):
            vocab = Vocabulary.get(vocab)
        inst = cls(vocab, name, parent)
        Session.add(inst)
        Session.flush()
        if labels:
            inst.set_labels(labels)
        return inst

    @classmethod
    def get_terms_q(cls, vocabulary_name, lang):
        s = Session
        q = s.query(cls.name, VocabularyLabel.label).join(Vocabulary, Vocabulary.name==vocabulary_name)\
                                                    .outerjoin(VocabularyLabel, VocabularyLabel.lang==lang)
        return q
    
    @classmethod
    def get_terms(cls, vocabulary_name, lang):
        q = cls.get_terms_q(vocabulary_name, lang)
        return [item[1] or item[0] for item in q]


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


def load_vocabulary(vocabulary_name, fpath, **vocab_config):
    try:
        vocab = Vocabulary.get(vocabulary_name)
        vocab.clear()
    except ValueError:
        vocab = Vocabulary.create(vocabulary_name, **vocab_config)
    
    with open(fpath, 'rt') as fh:
        r = csv.reader(fh)

        # first row is a header
        header = list(r.next())
        headers = header
        parent_name = None
        default = headers[0]

        # establish if we have a parent
        if header[0] == 'parent':
            if not vocab.has_relations:
                raise ValueError("Cannot use 'parent' colum if "
                                 "vocabulary that doesn't "
                                 "support relations")
            default = header[1]
            headers = header[1:]
            parent_name = header[0]
        
        for row in r:
            # per-term labels with header
            labels = dict(zip(headers, row))
            if not labels:
                continue
            parent = None
            default_label = labels[default]
            if parent_name:
                parent = VocabularyTerm.get(vocab, parent_name)
            VocabularyTerm.create(vocab, default_label, labels, parent=parent)
