# -*- coding: utf-8 -*-
#Copyright (C) 2007  Martin Špelina <shpelda at seznam dot cz>
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

import pygtk
pygtk.require('2.0')
import gtk
import threading
import re
import executor
class DeviceGui(threading.Thread):
  """Wraps user presentation of device"""

  def __init__(self, configuration, device):
    threading.Thread.__init__(self)
    self.device = device 
    self.actions = self.__create_actions(configuration)
    self.trayicon = self.__create_trayicon_from_configuration(configuration, device)
    uiManager = gtk.UIManager()
    uiManager.add_ui_from_string( self.__create_widget_description(configuration) )
    popup_actions = gtk.ActionGroup('popup_actions')
    for action in self.actions.keys():
      popup_actions.add_action(action)
    uiManager.insert_action_group(popup_actions)
    self.trayicon.connect('popup-menu', self.__popup_menu, uiManager.get_widget('/ui/traydevice'))
    self.__setup_sensitive()

  def run_action(self, action, commands):
    for c in commands:
      executor.execute(c, self.device)

  def __popup_menu(self,status_icon, button, activate_time, menu):
    self.__setup_sensitive()
    menu.popup(None,None,gtk.status_icon_position_menu, button, activate_time, status_icon)

  def __setup_sensitive(self):
    for a in self.actions:
      property_value = self.device.get_property(self.actions[a][0])
      expected=self.actions[a][1]
      a.set_property('sensitive',property_value == expected)
    
  def run(self):
    gtk.main()  

  def stop(self):
    gtk.main_quit()


  def __create_trayicon_from_configuration(self,configuration, device):
    available_icons = configuration.xpath('/traydevice/iconmap/icon/displayed_if')
    icon=None
    for i in available_icons:
      if device.get_property(i.get('ref')) == i.text:
        icon = i.getparent()
        break;
    if icon == None:
      map = configuration.xpath('/traydevice/iconmap')[0]
      return __create_trayicon(map.get('default_icon'), None)
    tooltip_configuration = icon.find('tooltip') 
    return self.__create_trayicon(icon.get('icon'), self.__create_tooltip(tooltip_configuration))

  def __create_tooltip(self, tooltip_configuration):
    if tooltip_configuration == None:
      return self.device.udi
    return re.sub(tooltip_configuration.get('regex'),
                  tooltip_configuration.get('replacement'),
                  self.device.get_property(tooltip_configuration.get('ref')))

  def __create_trayicon(self, icon_name, tooltip):
    stockitem = self.__get_gtk_stock_id(icon_name)
    trayicon = gtk.StatusIcon()
    trayicon.set_from_stock(stockitem)
    trayicon.set_tooltip(tooltip)
    return trayicon
   
  def __get_gtk_stock_id(self, icon_name):
    try:
      return eval(icon_name)
    except NameError:
      raise AssertionError('%s stockitem not found'%icon_name)
   
  def __create_widget_description(self, configuration):
    """create a menu from configuration, 
       popup is accessible at /ui/traydevice
    """ 
    menuitems = configuration.xpath('/traydevice/menuitem')
    menu ='<ui><popup name="traydevice">'
    action_id=0
    for menuitem in menuitems:
      action_label=menuitem.get('text')
      menu+='<menuitem name="%s" action="%s"/>'%(action_label, action_id)
      action_id += 1
    menu +='</popup>'
    menu +='</ui>'
    return menu

  def __create_actions(self, configuration):
    """create a dict of actions and their enabling properties"""
    actions = dict()
    menuitems = configuration.xpath('/traydevice/menuitem')
    action_id=0
    for menuitem in menuitems:
      enabled = menuitem.find('enabled_if')#TODO more conditions
      enabled_property=enabled.get('ref')
      enabled_value=enabled.text
      action_label=menuitem.get('text')
      action = gtk.Action(
        action_id,action_label,None,self.__get_gtk_stock_id(menuitem.get('icon')))
      action_id += 1
      commands=[]
      for c in menuitem.findall('command'):
        commands.append(c) 
      action.connect('activate', self.run_action, commands)
      actions[action]=[enabled_property, enabled_value]
    return actions

