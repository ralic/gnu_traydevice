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
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

import threading
from dbus.mainloop.glib import DBusGMainLoop
from dbus.mainloop.glib import threads_init
import dbus
import gobject
import logging


class Device(threading.Thread):
    """
        Wraps dbus connection to device
    """

    def __init__(self, device_file_path, device_removed_listener):
        threading.Thread.__init__(self)
        self.logger = logging.getLogger('Device')
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

        if self.__bool_match(self.get_property('DeviceIsRemovable'),'true'):
            udisks.connect_to_signal('DeviceChanged', self.__device_changed)
        else:
            udisks.connect_to_signal('DeviceRemoved', self.__device_removed)

        gobject.threads_init()
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
        return self.__complex_match(condition.getchildren()[0])
        pass

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
        value = self.get_property(key)
        for match in condition.items():
            if match[0] == 'key':
                continue
            if match[0] == 'string':
                if self.__string_match(value, match[1]):
                    return True
                continue
            if match[0] == 'int':
                if self.__int_match(value, match[1]):
                    return True
                continue
            if match[0] == 'bool':
                if self.__bool_match(value, match[1]):
                    return True
                continue
        pass

    def __string_match(self, value, match):
        return value == match

    def __int_match(self, value, match):
        return value == match

    def __bool_match(self, value, match):
        return value == match

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
           if self.__bool_match(self.get_property('DeviceIsMediaAvailable'),'false'):
                self.logger.debug(
                    'media from device %s has been removed' % cause)
                self.device_removed_listener.device_removed()
