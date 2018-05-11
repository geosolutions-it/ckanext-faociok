#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import logging
import traceback
from cStringIO import StringIO
from openpyxl import load_workbook

from ckan.common import _, ungettext
import ckan.plugins.toolkit as toolkit

from pylons import config
from ckan.lib.cli import CkanCommand

from ckanext.faociok.models import Vocabulary, VocabularyTerm, setup_models, Session, load_vocabulary

log = logging.getLogger(__name__)

class VocabularyCommands(CkanCommand):
    """
    Manage vocabularies in FAO-CIOK extension
    """

    summary = __doc__.split('\n')[0]
    usage = __doc__

    @property
    def usage(self):
        out = [self.__doc__]
        commands = self.get_commands()
        for ckey in sorted(commands.keys()):
            cmd = commands[ckey]
            cusage = self.command_usage(ckey, cmd)
            out.append(cusage)
        return '\n'.join(out)

    def cmd_list(self, *args, **kwargs):
        """
        List vocabularies
        """
        print(_('vocabularies:'))
        for voc in Vocabulary.get_all():
            print(_('vocabulary name: {}').format(voc.name))
            print(_('  has relations: {}').format(voc.has_relations))
            print()

    def cmd_create(self, vocabulary_name, has_relations=False, *args, **kwargs):
        """
        Create vocabulary

        syntax: create vocabulary_name [has_relations,default=no]

        """
        Vocabulary.create(vocabulary_name, bool(has_relations))
         

    def cmd_initdb(self, *args, **kwargs):
        """
        Init models
        """
        setup_models() 

    def cmd_load(self, vocabulary_name, path, *args, **kwargs):
        """
        Load vocabulary data

        syntax: load vocabulary_name path_to_source_file
        """
        with open(path, 'rt') as f:
            count = load_vocabulary(vocabulary_name, f)
            print(_('loaded {} terms from {} to {} vocabulary').format(count, path, vocabulary_name))

    def cmd_import_m49(self, vocabulary_name, in_file, *args, **kwargs):
        """
        Convert xlsx file with m49 data into vocabulary

        syntax: import_m49 in_file
        """
        wb = load_workbook(in_file)
        sheet = wb.active

        level1_cells = (5,6,)
        level1_parent_cell = None
        level2_cells = (8,9,)
        level2_parent_cell = 5
        countries_cells = (1,2,3,)
        countries_parent_cell = 8

        countries = []
        level1 = []
        level2 = []
        
        # 
        combine_data = ((countries_cells, countries_parent_cell, countries,),
                        (level1_cells, level1_parent_cell, level1,),
                        (level2_cells, level2_parent_cell, level2,))


        
        for row in sheet.iter_rows(min_row=6):
            for indexes, parent_cell, container in combine_data:
                # ( parent, data..)
                rdata = []
                if parent_cell is not None:
                    rdata.append(row[parent_cell-1].value)
                else:
                    rdata.append(parent_cell)

                for idx in indexes:
                    value = row[idx-1].value
                    rdata.append(value)
                container.append(rdata)
        for r in level1[:10]:
            print(r)
        for r in level2[:10]:
            print(r)
        for r in countries[:10]:
            print(r)
        
        csvdata = StringIO()


    def get_commands(self):
        """
        Return dictionary of command-> callable 
        """
        return dict([ (n[4:], getattr(self, n),) for n in dir(self) if n.startswith('cmd_')])
        
    def command_usage(self, cmd, callable):
        return '    {}\n     {}\n'.format(cmd, callable.__doc__.strip())

    def command(self):
        '''
        Parse command line arguments and call appropriate method.
        '''
        try:
            cmd = self.args[0]
        except IndexError:
            print(_("ERROR: missing command"))
            print(self.usage)
            return

        self._load_config()

        commands = self.get_commands()
        if not cmd in commands:
            print(_("ERROR: invalid command: {}").format(cmd))
            print(self.usage)
            return
        callable = commands[cmd]
        try:
            out = callable(*self.args[1:], **vars(self.options))
            Session.commit()
            return out
        except Exception, err:
            log.error(_("Can't execute %s with args %s: %s"), cmd, self.args[1:], err, exc_info=err)
            traceback.print_exc(err)
            print(_("Can't execute {} with args {}: {}").format(cmd, self.args[1:], err))
            print(self.command_usage(cmd, callable))
            return
