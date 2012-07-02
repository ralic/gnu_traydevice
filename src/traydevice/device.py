# -*- coding: utf-8 -*-
#Copyright (C) 2009    Martin Špelina <shpelda at gmail dot com>
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
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

from threading import Thread
from dbus.mainloop.glib import DBusGMainLoop
from dbus.mainloop.glib import threads_init
import dbus
import gobject
import logging

class PropertyResolver:
    """
        An implementation of boolean logic operations over properties  
    """
    def __init__(self, device):
        self.device = device
        
    def match(self, condition):
        """
            Return True if this device matches condition defined by
            xsd:T_condition
        """
        return self.__complex_match(condition.getchildren()[0])

    def __complex_match(self, condition):
        if 'and' == condition.tag:
            for child in condition.getchildren():
                if not self.__complex_match(child):
                    return False
            return True
        if 'or' == condition.tag:
            for child in condition.getchildren():
                if self.__complex_match(child):
                    return True
            return False
        if 'not' == condition.tag:
            return not self.__complex_match(condition.getchildren()[0])
        if 'match' == condition.tag:
            return self.__elementary_match(condition)

    def __elementary_match(self, condition):
        """ return True is this device matches condition definded by
            xsd:T_elementary_condition
        """
        key = condition.get('key')
        value = self.device.get_property(key)
        for match in condition.items():
            if match[0] == 'key':
                continue
            if match[0] == 'string':
                if self.string_match(value, match[1]):
                    return True
                continue
            if match[0] == 'int':
                if self.int_match(value, match[1]):
                    return True
                continue
            if match[0] == 'bool':
                if self.bool_match(value, match[1]):
                    return True
                continue
        pass

    def string_match(self, value, match):
        return value == match

    def int_match(self, value, match):
        return value == match

    def bool_match(self, value, match):
        return value == match
      
class UdisksDevice(Thread):
    """
        Wraps dbus connection to org.freedesktop.UDisks.Device
    """
    def __init__(self, device_file_path, device_removed_listener):
        Thread.__init__(self)
        self.logger = logging.getLogger('UdisksDevice')
        self.device_removed_listener = device_removed_listener
        DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SystemBus()
        _udisks = self.bus.get_object(
                                'org.freedesktop.UDisks',
                                '/org/freedesktop/UDisks')
        udisks = dbus.Interface(_udisks, 'org.freedesktop.UDisks')

        self.device_object_path = udisks.FindDeviceByDeviceFile(
                                                device_file_path)
        _dbus_object_proxy = self.bus.get_object(
                                    'org.freedesktop.UDisks',
                                    self.device_object_path)
        self.device = dbus.Interface(_dbus_object_proxy,
                                    'org.freedesktop.UDisks.Device')
        self.device_properties = dbus.Interface(_dbus_object_proxy,
                                    'org.freedesktop.DBus.Properties')
        
        self.resolver = PropertyResolver(self)

        if self.resolver.bool_match(self.get_property('DeviceIsRemovable'),'true'):
            udisks.connect_to_signal('DeviceChanged', self.__device_changed)
        else:
            udisks.connect_to_signal('DeviceRemoved', self.__device_removed)

        gobject.threads_init() #@UndefinedVariable
        threads_init()
        self.loop = gobject.MainLoop()

    def get_property(self, key):
        """
            Return actual value of device property
        """
        try:
            raw = self.device_properties.Get('org.freedesktop.UDisks.Device',
                                            key)
            if type(raw) == dbus.Boolean:
                if raw:
                    return 'true'
                else:
                    return 'false'
            else:
                return str(raw)
        except dbus.exceptions.DBusException:
            self.logger.warning('property "%s" not found on device' % key)
            return None
    def match(self, condition):
        """
            Return True if this device matches condition defined by
            xsd:T_condition
        """
        return self.resolver.match(condition);
    
    def run(self):
        """
           listens to device removed event,
           killing the application when device is removed
           this has to be invoked in separate thread so that it won;t block
           gui thread
        """
        self.loop.run()

    def stop(self):
        self.loop.quit()

    def __device_removed(self, cause):
        if self.device_object_path == cause:
            self.logger.debug(
                'device %s has been removed from system' % cause)
            self.device_removed_listener.device_removed()

    def __device_changed(self, cause):
        if self.device_object_path == cause:
            if ((self.__bool_match(self.get_property('DeviceIsOpticalDisc'),'true') and
                    self.__bool_match(self.get_property('OpticalDiscIsClosed'),'false')) 
            or (self.__bool_match(self.get_property('DeviceIsMediaAvailable'),'false'))):
                self.logger.debug(
                    'media from device %s has been removed' % cause)
                self.device_removed_listener.device_removed()
        
                
class Udisks2Device(Thread):
    """
        Wraps dbus connection to org.freedesktop.UDisks2.BlockDevice
    """
    def __init__(self, device_file_path, device_removed_listener):
      Thread.__init__(self)
      self.logger = logging.getLogger('Udisks2Device')
      self.device_removed_listener = device_removed_listener
      DBusGMainLoop(set_as_default=True)
      self.bus = dbus.SystemBus()
      
      self.resolver = PropertyResolver(self)
      
      udisks2proxy = self.bus.get_object('org.freedesktop.UDisks2','/org/freedesktop/UDisks2')
      object_manager =  dbus.Interface(udisks2proxy, 'org.freedesktop.DBus.ObjectManager')
      object_manager.connect_to_signal('InterfacesRemoved', self.__interface_removed, byte_arrays=True)
      managed  = object_manager.GetManagedObjects(byte_arrays=True)
      
      self.object_path = self.get_object_path(managed, device_file_path)
      self.logger.info('Connected to udisks object_path:%s'%self.object_path)
      
      gobject.threads_init() #@UndefinedVariable
      threads_init()
      self.loop = gobject.MainLoop()
    
    def get_object_path(self, managed, device_file_path):
      from os.path import realpath,samefile
      from dbustools import dbus_to_string
      for object_path, interfaces in managed.items():
        if not 'org.freedesktop.UDisks2.Block' in interfaces:
          continue
        block = interfaces['org.freedesktop.UDisks2.Block']
        if samefile(dbus_to_string(block['Device']), realpath(device_file_path)):
          return object_path;
      return None
        
    def get_property(self, key):
      return None
    
    def run(self):
        self.logger.debug('Udisks2Device Started')
        self.loop.run()
    
    def stop(self):
        self.loop.quit()
    
    def match(self, condition):
        return self.resolver.match(condition);
      
    def __interface_removed(self, object_path, interfaces):
      device_removed_apis=[
        'org.freedesktop.UDisks2.BlockDevice'# — Low-level Block Device
        ,'org.freedesktop.UDisks2.Filesystem'# — Block device containing a mountable filesystem
        ,'org.freedesktop.UDisks2.Swapspace'# — Block device containing swap data
        ,'org.freedesktop.UDisks2.Encrypted'# — Block device containing encrypted data
                           ]
      if self.object_path == object_path:
        for api in device_removed_apis:
          if api in interfaces:
            self.logger.info('Api %s of device %s has been removed from system.' %(api, object_path))
            self.device_removed_listener.device_removed()
