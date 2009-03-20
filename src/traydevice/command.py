# -*- coding: utf-8 -*-
#Copyright (C) 2009    Martin Špelina <shpelda at seznam dot cz>
#
#This program is free software; you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation; either version 2 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA

import subprocess
import logging


class Command:
    """
        Class wrapping one command to be executed
    """

    def __init__(self, command_configuration, device):
        """
            Command initialization
        """
        self.logger = logging.getLogger('Command')
        self.device = device
        self.configuration = command_configuration

    def execute(self):
        """
            Invoke configured command
        """
        args = [self.configuration.get('executable')]
        for arg in self.configuration.iterchildren():
            if arg.tag == 'arg':
                args.append(arg.text)
            if arg.tag == 'ref':
                args.append(self.device.get_property(arg.text))

        self.logger.debug('Executing:'+str(args))
        command = subprocess.Popen(args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        result = command.communicate()
        result = command.returncode, result
        self.logger.debug('Result:'+str(result))
        return result
