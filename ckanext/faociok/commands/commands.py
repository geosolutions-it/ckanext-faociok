#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import logging
import traceback

from ckan.common import _, ungettext
import ckan.plugins.toolkit as toolkit

from pylons import config
from ckan.lib.cli import CkanCommand

from ckanext.faociok.models import setup_models, Session

log = logging.getLogger(__name__)

class FAOCIOKCommand(CkanCommand):
    """Misc commands for FAO-CIOK extension.    
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
         
    def cmd_initdb(self, *args, **kwargs):
        """Init DB with FAO-CIOK model.
        """
        setup_models() 

    def get_commands(self):
        """
        Return dictionary of command-> callable 
        """
        return dict([ (n[4:], getattr(self, n),) for n in dir(self) if n.startswith('cmd_')])
        
    def command_usage(self, cmd, callable):
        return '    {}\n       {}\n'.format(cmd, callable.__doc__.strip())

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
