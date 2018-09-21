#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import json
import csv

from ckan.common import _, ungettext
from ckan.model import Package, PackageExtra, Session

from sqlalchemy import types, Column, ForeignKey, Index, Table, select
from sqlalchemy import orm, and_, or_, desc, distinct, func, cast, literal, inspect, case, desc
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
    VOCABULARY_AGROVOC = 'agrovoc'

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
        sq = Session.query(VocabularyTerm.id).filter(VocabularyTerm.vocabulary_id==self.id)
        Session.query(VocabularyLabel)\
                   .filter(VocabularyLabel.term_id.in_(sq.subquery())).delete(synchronize_session=False)

        #for vl in q:
        #    Session.delete(vl)
        sq.delete()

        #for vl in q:
        #    Session.delete(vl)
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

    def clear_labels(self):
        Session.query(VocabularyLabel).filter(VocabularyLabel.term_id==self.id).delete()
        Session.flush()

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
    def get_by_id(cls, item_id):
        return Session.query(cls).filter(cls.id==item_id).one()

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

    def update(self, labels=labels, parent=None, properties=None):
        self.clear_labels()
        self.set_labels(labels)
        self.properties = properties or {}
        Session.add(self)
        Session.flush()

    @classmethod
    def get_term(cls, vocabulary_name, *names):
        s = Session
        labels_q = or_(*[VocabularyLabel.label == n for n in names])
        names_q = or_(*[VocabularyTerm.name == n for n in names])
        scoring = case(
                       [
                        [and_(VocabularyTerm.name.in_(names),
                             VocabularyLabel.label.in_(names)), 3],
                        [VocabularyTerm.name.in_(names), 2],
                        [VocabularyLabel.label.in_(names), 1],
                       ],
                      else_=0)
        score = scoring.label('score')
        q = s.query(cls, scoring.label('score')).join(Vocabulary, Vocabulary.name==vocabulary_name)\
                        .outerjoin(VocabularyLabel, VocabularyLabel.term_id==cls.id)\
                        .filter(or_(labels_q, names_q))\
                        .order_by(desc(score))
        return q

    @classmethod
    def get_terms_q(cls, vocabulary_name, lang, include_dataset_count=False, is_multiple=False, filters=None, order_by=None):
        s = Session
        if not include_dataset_count:
            q = s.query(cls.name, VocabularyLabel.label, cls.depth, cls.id).join(Vocabulary)\
                                                        .outerjoin(VocabularyLabel)\
                                                        .filter(Vocabulary.name==vocabulary_name,
                                                                VocabularyLabel.lang==lang)
            if order_by:
                q = q.order_by(*order_by)
            else:
                q = q.order_by(cls.name)
        else:
            if is_multiple:
                oth = inspect(PackageExtra)
                value_cond = '{} =any({}::varchar[])'.format(cls.__table__.c['name'],
                                                                oth.c['value'])
            else:
                #value_cond = PackageExtra.value == cls.name
                value_cond = PackageExtra.value == cls.name

            q = s.query(cls.name, VocabularyLabel.label, cls.depth, cls.id, func.count(distinct(Package.id)).label('cnt')).join(Vocabulary)\
                                                        .outerjoin(VocabularyLabel)\
                                                        .outerjoin(PackageExtra,
                                                              and_(PackageExtra.key=='fao_{}'.format(vocabulary_name),
                                                                   value_cond))\
                                                        .outerjoin(Package, 
                                                                and_(Package.id==PackageExtra.package_id,
                                                                     Package.type=='dataset',
                                                                     Package.state=='active'))\
                                                        .filter(Vocabulary.name==vocabulary_name,
                                                                VocabularyLabel.lang==lang)\
                                                        .group_by(cls.name, VocabularyLabel.label, cls.depth, cls.id)
            if order_by:
                q = q.order_by(*order_by)
            else:
                q = q.order_by(desc('cnt'), cls.name)
        if filters:
            q = q.filter(*filters)
        return q
    
    @classmethod
    def get_terms(cls, vocabulary_name, lang, include_dataset_count=False, is_multiple=False, filters=None, order_by=None):
        """
        Returns list of terms for vocabulary
        @param vocabulary_name name of vocabulary
        @param lang 2-char lang code
        @param include_dataset_count returns number of active datasets using this term (default: no)
        @param filters addictional terms query filters_by arguments

        @rtype list of items:
                * term name
                * localized label or term name (if label is not available)
                * depth
                * term id
                (optionally, if include_dataset_count flag is set):
                * dataset_count
        """
        _filters=cls.make_filters(filters)
        q = cls.get_terms_q(vocabulary_name,
                            lang,
                            include_dataset_count=include_dataset_count,
                            is_multiple=is_multiple,
                            filters=_filters,
                            order_by=order_by)
        keys = ('value', 'text', 'depth', 'id',)
        if include_dataset_count:
            keys += ('dataset_count',)

        def make_row(row):
            out = dict(zip(keys, row))
            out['text'] = row[1] or row[0]
            formatted_elements = '-' * out['depth'], ' ' if out['depth'] else '', out['text'],
            out['text_raw'] = out['text']
            #out['text'] = u'{}{}{}'.format(*formatted_elements)
            return out

        return [make_row(row) for row in q]

    @classmethod
    def make_filters(cls, filters):
        """
        Translate dictionary of key->value into query.filter(..) values from VocabularyTerm
        @param filters dictionary of VocabularyTerm columns->values or list of filters
        """
        # no filters, bye
        if not filters:
            return
        # anything else than dict, we assume it's already a list of filters
        if not isinstance(filters, dict):
            return filters
        
        out = []
        for k,v in filters.items():
            attr = getattr(VocabularyTerm, k, None)
            if not attr:
                pass
            out.append(attr == v)
        return out

    @classmethod
    def get_most_frequent_parent(cls, vocabulary, lang, multiple=False, limit=None):

        children = orm.aliased(VocabularyTerm, name='children_vocab_term')
        oth = inspect(PackageExtra)

        if multiple:
            value_cond = '{} =any({}::varchar[])'.format('children_vocab_term.name',
                                                         oth.c.value)
        else:
            #value_cond = PackageExtra.value == cls.name
            value_cond = PackageExtra.value == children.name
        
        q = Session.query(VocabularyTerm.id, VocabularyTerm.name, func.count(1).label('cnt'))\
                   .join(Vocabulary, and_(Vocabulary.id==VocabularyTerm.vocabulary_id,
                                          Vocabulary.name==vocabulary))\
                   .join(children, VocabularyTerm.id==children.parent_id)\
                   .join(PackageExtra,
                              and_(PackageExtra.key=='fao_{}'.format(vocabulary),
                                     value_cond))\
                   .group_by(VocabularyTerm.id, VocabularyTerm.name)\
                   .order_by(desc('cnt'), VocabularyTerm.name)
        if limit:
            q = q.limit(limit)

        out = []
        for item in q:
            parent_id = item[0]
            parent_name = item[1]
            count = item[2]
            parent = VocabularyTerm.get_by_id(parent_id)
            text = parent.get_label(lang).label or parent.get_label('en').label or v
            out.append({'name': parent_name,
                        'dataset_count': count,
                        'value': parent_name,
                        'text': text})
        return out

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
            log.info(_("Parent column found at idx %s"), idx)
            parent_idx = idx
        elif header == "term":
            log.info(_("Term column found at idx %s"), idx)
            term_idx = idx
        elif not header.startswith('lang:') and not header.startswith('property:'):
            log.info(_("Column %s will not be stored"), header)
        idx = idx + 1

    # establish if we have a parent
    if parent_idx is not None and not vocab.has_relations:
        raise ValueError(_("Cannot use 'parent' colum if "
                           "vocabulary that doesn't support relations"))

    if term_idx is None:
        raise ValueError(_("Term column not found"))
    
    no_parent_yet = []
    def rows_generator():
        input_row_count = 0
        for r in rows:
            input_row_count += 1
            yield r
        no_parent_count = 0
        while no_parent_yet:
            no_parent_count += 1
            yield no_parent_yet.pop(0)
            if len(no_parent_yet) > input_row_count:
                raise ValueError("no parent count {} above input count: {}".format(no_parent_count,
                                                                                   input_row_count))
            #if no_parent_count % 100:
            #    print('got {} no parent rows'.format(len(no_parent_yet)))
    for row in rows_generator():
        # all data for row
        _data = dict(zip(headers, row))
        # properties are cells for which header starts with 'property:' prefix
        properties = dict( (k[len('property:'):],v,) for k,v in _data.items() if k.startswith('property:') and v)
        # labels are cells for which header starts with 'lang:'
        labels = dict( (k[len('lang:'):],v,) for k,v in _data.items() if k.startswith('lang:'))

        term = row[term_idx]
        parent = row[parent_idx] if parent_idx is not None else None

        if not term:
            # print(_("Skipping row with no term: {}").format(_data))
            continue
        
        #if parent and parent == term:
        #    print(_("Skipping row with parent the same as itself: {}".format(_data)))
        #    continue


        parent_from_db = VocabularyTerm.get(vocab, parent) if parent else None
        if parent and not parent_from_db:
            log.info(_("Postpoining %s term - no %s parent in db yet"), _data['term'], _data['parent'])
            no_parent_yet.append(row)
            continue

        term_from_db = VocabularyTerm.get(vocab, term)
        # print(_("TERM FROM DB ID[{}] DB[{}] ").format(term, term_from_db))
        if term_from_db:
            term_from_db.update(labels=labels, parent=parent_from_db, properties=properties)
            #print(_("Updating existing term: INPUT [{}] DB [{}] ").format(_data, term_from_db))
        else:
            # print(_("Term [{}] has PARENT [{}] [{}] ").format(term, parent, parent_from_db))
            VocabularyTerm.create(vocab, term, labels, parent=parent_from_db, properties=properties)
            if not VocabularyTerm.get(vocab, term):
                log.error(_("ERROR: TERM NOT CREATED  vocab[%s] term[%s] data[%s]"), vocab, term, _data)
        
        counter += 1
    return counter
