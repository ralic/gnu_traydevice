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

import pygtk
pygtk.require('2.0')
import gtk
import threading
import re
from command import Command


class DeviceGui(threading.Thread):
    """
        User presentation of device
    """

    def __init__(self, configuration, device):
        threading.Thread.__init__(self)
        self.device = device
        self.actions = self.__create_actions(configuration)
        self.trayicon = \
            self.__create_trayicon_from_configuration(configuration)
        uiManager = gtk.UIManager()
        uiManager.add_ui_from_string(
            self.__create_widget_description(configuration))
        popup_actions = gtk.ActionGroup('popup_actions')
        for action in self.actions.keys():
            popup_actions.add_action(action)
        uiManager.insert_action_group(popup_actions)
        self.trayicon.connect('popup-menu',
            self.__popup_menu,
            uiManager.get_widget('/ui/traydevice'))
        self.__setup_sensitive()

    def run_action(self, action, commands):
        """
            Menu callback
        """
        for c in commands:
            c.execute()

    def __popup_menu(self, status_icon, button, activate_time, menu):
        self.__setup_sensitive()
        menu.popup(None,
          None,
          gtk.status_icon_position_menu,
          button,
          activate_time,
          status_icon)

    def __setup_sensitive(self):
        """
            Enable/disable menu entries based on configuration
        """
        for a in self.actions:
            a.set_property('sensitive', self.device.match(self.actions[a][0]))

    def run(self):
        """
            Start being displayed
        """
        gtk.main()

    def stop(self):
        """
            Stop being displayed
        """
        gtk.main_quit()

    def __create_trayicon_from_configuration(self, configuration):
        """
            Create a systray icon from T_iconmap
        """
        available_icons = \
            configuration.xpath('/traydevice/iconmap/icon/displayed_if')
        icon = None
        for i in available_icons:
            if self.device.match(i):
                icon = i.getparent()
                break
        if icon == None:
            map = configuration.xpath('/traydevice/iconmap')[0]
            return \
                self.__create_trayicon(map.get('default_icon'),
                  None)
        tooltip_configuration = icon.find('tooltip')
        return self.__create_trayicon(
            icon.get('icon'),
            self.__create_tooltip(tooltip_configuration))

    def __create_tooltip(self, tooltip_configuration):
        if tooltip_configuration == None:
            return self.device.device_object_path
        tooltip = Command(tooltip_configuration, self.device).execute()
        return tooltip[1][0]

    def __create_trayicon(self, icon_name, tooltip):
        stockitem = self.__get_gtk_stock_id(icon_name)
        trayicon = gtk.StatusIcon()
        trayicon.set_from_stock(stockitem)
        trayicon.set_tooltip(tooltip)
        return trayicon

    def __get_gtk_stock_id(self, icon_name):
        try:
            return eval(icon_name)
        except:
            raise AssertionError('\'%s\' stockitem not found' % icon_name)

    def __create_widget_description(self, configuration):
        """
            Create gtk popup menu from configuration,
            popup is accessible at /ui/traydevice
        """
        menuitems = configuration.xpath('/traydevice/menuitem')
        menu = '<ui><popup name = "traydevice">'
        action_id = 0
        for menuitem in menuitems:
            action_label = menuitem.get('text')
            menu += '<menuitem name = "%s" action = "%s"/>'\
                % (action_label, action_id)
            action_id += 1
        menu += '</popup>'
        menu += '</ui>'
        return menu

    def __create_actions(self, configuration):
        """
            Create a dictionary of menu actions and
            commands assigned to them
        """
        actions = dict()
        menuitems = configuration.xpath('/traydevice/menuitem')
        action_id = 0
        for menuitem in menuitems:
            action_label = menuitem.get('text')
            enabled_if = menuitem.find('enabled_if')
            action = gtk.Action(action_id,
                action_label,
                None,
                self.__get_gtk_stock_id(menuitem.get('icon')))
            action_id += 1
            commands = []
            for c in menuitem.findall('command'):
                commands.append(Command(c, self.device))
            action.connect('activate', self.run_action, commands)
            actions[action] = [enabled_if]
        return actions
