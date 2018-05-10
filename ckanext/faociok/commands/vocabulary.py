#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import logging
import traceback

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
        print('vocabularies:')
        for voc in Vocabulary.get_all():
            print('vocabulary name: {}'.format(voc.name))
            print('  has relations: {}'.format(voc.has_relations))
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
        load_vocabulary(vocabulary_name, path)

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
            print("ERROR: missing command")
            print(self.usage)
            return

        self._load_config()

        commands = self.get_commands()
        if not cmd in commands:
            print("ERROR: invalid command: {}".format(cmd))
            print(self.usage)
            return
        callable = commands[cmd]
        try:
            out = callable(*self.args[1:], **vars(self.options))
            Session.commit()
            return out
        except Exception, err:
            log.error("Can't execute %s with args %s: %s", cmd, self.args[1:], err, exc_info=err)
            traceback.print_exc(err)
            print("Can't execute {} with args {}: {}".format(cmd, self.args[1:], err))
            print(self.command_usage(cmd, callable))
            return
