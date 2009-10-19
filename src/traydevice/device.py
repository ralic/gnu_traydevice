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

import threading
from dbus.mainloop.glib import DBusGMainLoop
from dbus.mainloop.glib import threads_init
import dbus
import gobject

class Device(threading.Thread):
  """Wraps the device itself"""

  def __init__(self, udi, device_removed_listener):
    """
        Initialize the device
        udi .. hal identifier of the device
        device_removed_listener ... object, whose device_removed method gets invoked in case device gets removed 
    """
    threading.Thread.__init__(self)
    self.device_removed_listener = device_removed_listener
    self.udi=udi 

    #setup a connection to dbus & hal
    DBusGMainLoop(set_as_default=True)
    self.bus = dbus.SystemBus()
    self.hal_device = self.__create_device(self.udi)
    self.bus.add_signal_receiver(self.__device_removed,
      "DeviceRemoved",
      "org.freedesktop.Hal.Manager",
      "org.freedesktop.Hal",
      "/org/freedesktop/Hal/Manager")
    gobject.threads_init()
    threads_init()      
    self.loop=gobject.MainLoop()

  def get_property(self, key):
    """return actual value of device property"""
    try:
      raw = self.__get_property(key)
      if type(raw) == dbus.Boolean:
        if str(raw)=='1':
          return 'true'
        else:
          return 'false'
      else:
        return str(raw)
    except dbus.exceptions.DBusException:
      print 'Warning:property "%s" not found on device hierarchy'%key
      return None

  def run(self):
    """listens to hal event, killing the application when device is removed
        this has to be invoked in separate thread so that it won;t block gui thread
    """  
    self.loop.run()
  
  def stop(self):
    self.loop.quit()

  def __device_removed(self, cause):
      if self.udi== cause:
        print 'device %s has been removed from system'%self.udi
        self.device_removed_listener.device_removed()

  def __create_device(self, udi):
      return dbus.Interface(self.bus.get_object('org.freedesktop.Hal', udi)
            , 'org.freedesktop.Hal.Device')

  def __get_property(self, key, hal_device=None):
    """ recursively read value of hal property of given name """
    """ reads it from paren udi if it is not accessible from actual one """
    if hal_device == None:
      hal_device = self.hal_device
    try:
      return hal_device.GetProperty(key) 
    except dbus.exceptions.DBusException:
      parent_udi = hal_device.GetProperty('info.parent') 
      parent_object = self.__create_device(parent_udi)
      return self.__get_property(key, parent_object)
