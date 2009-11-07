# -*- coding: utf-8 -*-
#Copyright (C) 2009  Martin Špelina <shpelda at seznam dot cz>
#
#This program is free software; you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation; either version 2 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

import sys
import signal
from lxml import etree
from optparse import OptionParser
import os
import shutil
 
import device 
import gui

def get_resource(resource):
  """retrieve files from sources"""
  return os.path.join(os.path.dirname(__file__), resource)

class Main:
  
  def __init__(self, argv):
    default_config_file=os.path.expanduser('~/.config/traydevice/default.xml')
    parser = OptionParser(usage="%prog [options] udi", version="%prog 1.0")
    parser.add_option('-c', '--configfile', dest='configfile',
                  help='read configuration from FILE instead of default in %s'%default_config_file, metavar='FILE')
    (opts, args) = parser.parse_args()
    configfile = opts.configfile 
    if configfile == None:
      configfile = default_config_file
      if not os.path.exists(default_config_file):
        if not os.path.exists(os.path.dirname(default_config_file)):
          os.makedirs(os.path.dirname(default_config_file))
        shutil.copyfile(get_resource('example-configuration.xml'), default_config_file)

    configuration = self.__open_configuration(configfile)
    if len(args)!=1:
      raise AssertionError('udi argument is required')
    self.device = device.Device(args[0], self)
    self.gui = gui.DeviceGui(configuration, self.device)

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


  def __open_configuration(self,configuration_file):
    xsdfile = open(get_resource('configuration.xsd'))
    try:
      schema_root = etree.XML( xsdfile.read() )
    finally:
      xsdfile.close()
    schema = etree.XMLSchema(schema_root)
    parser = etree.XMLParser(schema=schema)

    configuration_file=open(configuration_file)
    try:
      root = etree.fromstring(configuration_file.read(), parser)
    finally:
      configuration_file.close()
    return root



if __name__=="__main__":
  signal.signal(signal.SIGINT, signal.SIG_DFL)

  main = Main(sys.argv)
  main.start()

