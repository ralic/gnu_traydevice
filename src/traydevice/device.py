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
from dbustools import org_freedesktop_DBus_Properties as DBusProperties
from dbustools import org_freedesktop_DBus_ObjectManager as DBusObjectManager
from dbustools import org_freedesktop_DBus_Introspectable as DBusIntrospectable
from numpy.distutils.fcompiler import str2bool


class PropertyResolver:
    """
        An implementation of boolean logic operations over properties  
    """
    def __init__(self, property_accessor):
        self.property_accessor = property_accessor
        self.logger = logging.getLogger(__name__)

    def match(self, condition):
        """
            Return True if this device matches condition defined by
            xsd:T_condition
        """
        return self.__complex_match(filter(self.is_not_ignored_tag, condition)[0])
    
    def is_not_ignored_tag(self, condition):
      from lxml.etree import Comment
      return condition.tag != Comment
    
    def __complex_match(self, condition):
        if 'and' == condition.tag:
            for child in filter(self.is_not_ignored_tag, condition):
                self.logger.debug('testing %s'%child)              
                if not self.__complex_match(child):
                    return False
            return True
        if 'or' == condition.tag:
            for child in filter(self.is_not_ignored_tag, condition):
                if self.__complex_match(child):
                    return True
            return False
        if 'not' == condition.tag:
            return not self.__complex_match(filter(self.is_not_ignored_tag, condition)[0])
        if 'match' == condition.tag:
            return self.__elementary_match(condition)
          
        self.logger.error('%s tag(%s) not recognized'%(condition, condition.tag))

    def __elementary_match(self, condition):
        """ return True is this device matches condition definded by
            xsd:T_elementary_condition
        """
        key = condition.get('key')
        value = self.property_accessor.get_property(key)
        for match in condition.items():
            if match[0] == 'key':
                continue
            match_method = eval('self.%s_match'%match[0])
            result = match_method(value, match[1])
            self.logger.debug('%s value:%s,match:%s, result:%s'%(match_method, value, match, result))
            if match_method(value, match[1]):
              return True

    def string_match(self, value, match):
        return str(value) == match

    def int_match(self, value, match):
        return value == match

    def bool_match(self, value, match):
        value = self.str2bool(value)
        match = self.str2bool(match)
        return match == value
      
    
    def str2bool(self, v):
      try:
        v = v.lower()
      except:
        pass
      return v in (True, "yes", "true", "t", "1")
      
    def regex_match(self, value, match):
        import re
        return re.match(match, value) is not None

class PropertyAccessor:
  """
    Provides a way to access properties 
  """
  def __init__(self, system_bus, bus_name, device_object_path):
    self.logger = logging.getLogger(__name__)
    self.system_bus = system_bus
    self.BUS_NAME = bus_name
    self.DEVICE_OBJECT_PATH = device_object_path

  def get_property(self, key):
    """
        Return actual value of device property
    """
    try:
        keylist = self.parse_key(key)
        keylist.reverse()
        raw = self.get_property_from_keylist(keylist, self.DEVICE_OBJECT_PATH)
        from dbustools import dbus_to_object
        result = dbus_to_object(raw)
        if result is None:
          result=''
        self.logger.debug("get_property %s:dbus-value=%s, result='%s'",key, raw, result)
        return result
    except dbus.exceptions.DBusException:
        self.logger.warning('property "%s" not found on device' % key, exc_info=1)
        return None

  def get_property_from_keylist(self, keylist, device_object_path):
    """ Recursively retrieve value of property 'k' at keylist[0](i,k) where value at keylist[x,x>1](i,k) means object name for keylist[x-1](i,k)"""
    interface_name, property_name = keylist.pop()
    dbus_object_proxy = self.system_bus.get_object(
                          self.BUS_NAME,
                          device_object_path)
    if not interface_name:
      introspection = DBusIntrospectable(dbus_object_proxy)
      metadata = introspection.Introspect()
      available_properties = introspection.get_interface_properties(metadata)
      match=[]
      for interface_name, properties in available_properties.items():
        if property_name in properties:
          match.append(interface_name)
      if len(match)==1:
        interface_name = match[0]
      else:
        if match:
          raise ValueError("Unable to unique identify property name'%s', possible interfaces are '%s'"%(property_name, ','.join(match)))#FIXME:use custom exception
        else:
          raise ValueError("No interface contains property name '%s'"%property_name)#FIXME:use custom exception
    property_value = DBusProperties(dbus_object_proxy).Get(interface_name, property_name)
    self.logger.debug('get_property_from_keylist %s.%s:%s',interface_name, property_name, property_value)
    if keylist:
      return self.get_property_from_keylist(keylist, property_value)
    else:
      return property_value

  def parse_key(self, key):
    """
      Accepted property keys are in format [/][interfacename.]propertyName[/[interfacename.]propertyName]*
      where interfacename is completely optional.
      '/' means link-target so /Drive/Media means : read ..Block property 'Drive', fetch object referenced there(if any) and return it's 
      property 'Media'
      returns list(tuple(interface, local_key)) 
    """
    result=[]
    for lk in key.split('/'):
      lk=lk.strip('./')
      lk=lk.strip();
      if not lk:
        continue
      interface = None
      property_key = lk
      if '.' in lk:
        last_dot = lk.rfind('.')
        i = lk[0:last_dot]
        k = lk[last_dot+1:]
        i=i.strip()
        if i:
          interface = i
        property_key = k.strip()
      result.append((interface, property_key))
    return result

def create_device(device_file_path, device_removed_listener, configured_backend='org.freedesktop.UDisks'):

  DBusGMainLoop(set_as_default=True)
  mainloop = gobject.MainLoop()
  system_bus =  dbus.SystemBus()
  backend_init = {'org.freedesktop.UDisks': 'backend_org_freedesktop_UDisks'
                , 'org.freedesktop.UDisks2': 'backend_org_freedesktop_Udisks2'
               }
  gobject.threads_init() #@UndefinedVariable
  threads_init()
  backend = eval(backend_init[configured_backend])(system_bus, device_file_path)
  return Device(device_removed_listener, mainloop, system_bus, backend)

class Device(Thread):
  def __init__(self, device_removed_listener, mainloop, system_bus, backend):
    Thread.__init__(self)
    self.logger = logging.getLogger(__name__)
    self.logger.info('Connected to %s object_path:%s'%(backend, backend.DEVICE_OBJECT_PATH))
    self.accessor = PropertyAccessor(system_bus, backend.BUS_NAME, backend.DEVICE_OBJECT_PATH)
    self.resolver = PropertyResolver(self.accessor)
    backend.register_device_removed_listener(self, system_bus, device_removed_listener)
    self.loop = mainloop

  def get_property(self, key):
      """
          Return actual value of device property
      """
      return self.accessor.get_property(key)

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


class backend_org_freedesktop_UDisks:
  BUS_NAME='org.freedesktop.UDisks'
  def __init__(self, system_bus, device_file_path):
    self.logger = logging.getLogger(__name__)
    _udisks = system_bus.get_object(self.BUS_NAME, '/org/freedesktop/UDisks')
    self.udisks = dbus.Interface(_udisks, 'org.freedesktop.UDisks')
    self.DEVICE_OBJECT_PATH = self.udisks.FindDeviceByDeviceFile(device_file_path)

  def register_device_removed_listener(self, device, system_bus, device_removed_listener):
    if device.get_property('DeviceIsRemovable'):
        self.udisks.connect_to_signal('DeviceChanged', self.__device_changed)
    else:
        self.udisks.connect_to_signal('DeviceRemoved', self.__device_removed)

  def __device_removed(self, cause):
      if self.DEVICE_OBJECT_PATH == cause:
          self.logger.debug(
              'device %s has been removed from system' % cause)
          self.device_removed_listener.device_removed()

  def __device_changed(self, cause):
      if self.DEVICE_OBJECT_PATH == cause:
          if (self.device.get_property('DeviceIsOpticalDisc') 
                and not self.device.get_property('OpticalDiscIsClosed')
              ) or not self.device.get_property('DeviceIsMediaAvailable'):
              self.logger.debug('Media from device %s has been removed' % cause)
              self.device_removed_listener.device_removed()


class backend_org_freedesktop_Udisks2:
  BUS_NAME='org.freedesktop.UDisks2'
  def __init__(self, system_bus, device_file_path):
    self.logger = logging.getLogger(__name__)
    udisks2proxy = system_bus.get_object(self.BUS_NAME,'/org/freedesktop/UDisks2')
    self.object_manager = DBusObjectManager(udisks2proxy)
    managed  = self.object_manager.GetManagedObjects()
    self.DEVICE_OBJECT_PATH = self.__get_object_path(managed, device_file_path)

  def register_device_removed_listener(self, device, system_bus, device_removed_listener):
    self.object_manager.connect_to_InterfacesRemoved(self.__interface_removed)

  def __get_object_path(self, managed, device_file_path):
    from os.path import realpath,samefile
    from dbustools import dbus_to_string
    for object_path, interfaces in managed.items():
      if not 'org.freedesktop.UDisks2.Block' in interfaces:
        continue
      block = interfaces['org.freedesktop.UDisks2.Block']
      if samefile(dbus_to_string(block['Device']), realpath(device_file_path)):
        return object_path;
    return None

  def __interface_removed(self, object_path, interfaces):
    device_removed_apis=[
      'org.freedesktop.UDisks2.Block'# — Low-level Block Device
      ,'org.freedesktop.UDisks2.Filesystem'# — Block device containing a mountable filesystem
      ,'org.freedesktop.UDisks2.Swapspace'# — Block device containing swap data
      ,'org.freedesktop.UDisks2.Encrypted'# — Block device containing encrypted data
                         ]
    if self.DEVICE_OBJECT_PATH == object_path:
      for api in device_removed_apis:
        if api in interfaces:
          self.logger.info('Api %s of device %s has been removed from system.' %(api, object_path))
          self.device_removed_listener.device_removed()
