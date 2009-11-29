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
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

import sys
import signal
from lxml import etree
from optparse import OptionParser
import os
import shutil
from xdg import BaseDirectory
import logging
import logging.config

import device
import gui


def get_resource(resource):
    """
        Retrieve files from sources
    """
    return os.path.join(os.path.dirname(__file__), resource)


def get_config_file(filename):
    """
        Retrieve path to configuration file identified by
        filename. If file does not exist at location defined by
        XDG_CONFIG_HOME, it will be created with default values.
    """
    xdg = os.path.join(
        BaseDirectory.save_config_path('traydevice'), filename)
    if not os.path.exists(xdg):
        shutil.copyfile(get_resource(filename), xdg)
    return xdg


class Main:

    def __init__(self):
        """
            Initialize traydevice, parse command line, read configuration
        """
        configfile = get_config_file('default.xml')
        parser = OptionParser(usage="%prog [options] udi", version="%prog 1.2")
        parser.add_option('-c', '--configfile', dest='configfile',
            help='read configuration from FILE instead of default in %s' %
                configfile, metavar='FILE')
        (opts, args) = parser.parse_args()
        if opts.configfile != None:
            configfile = opts.configfile

        if len(args) != 1:
            logging.getLogger('Main').error('udi argument is required')
            sys.exit(1)
        try:
            configuration = self.__open_configuration(configfile)
        except Exception as e:
            logging.getLogger('Main').error(
                'Cannot read configuration file \'%s\' (%s)'
                %(configfile, e))
            sys.exit(1)
        try:            
            self.device = device.Device(args[0], self)
        except Exception as e:
            logging.getLogger('Main').error(
                'Cannot access hal device \'%s\' (%s)'
                %(args[0], e)) 
            sys.exit(1)
        try:
            self.gui = gui.DeviceGui(configuration, self.device)
        except Exception as e:
            logging.getLogger('Main').error(
                'Gui construction failed. (%s)' % e) 
            sys.exit(1)

    def start(self):
        """
            Start activity
        """
        self.gui.start()
        self.device.start()

    def stop(self):
        """
            Stop activity, finish the program
        """
        self.gui.stop()
        self.device.stop()

    def device_removed(self):
        """
            Device.device_removed_listener callback
        """
        self.stop()

    def __open_configuration(self, configuration_file):
        xsdfile = open(get_resource('configuration.xsd'))
        try:
            schema_root = etree.XML(xsdfile.read())
        finally:
            xsdfile.close()
        schema = etree.XMLSchema(schema_root)
        parser = etree.XMLParser(schema=schema)

        configuration_file = open(configuration_file)
        try:
            root = etree.fromstring(configuration_file.read(), parser)
        finally:
            configuration_file.close()
        return root


def main():
    """
        Start traydevice
    """
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    logging.config.fileConfig(get_config_file('logging.conf'))
    main = Main()
    main.start()
if __name__ == "__main__":
    main()
