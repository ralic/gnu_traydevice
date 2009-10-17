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

import subprocess

def __construct_args(command_configuration, device):
  args=[command_configuration.get('executable')]
  for arg in command_configuration.iterchildren():
    if arg.tag == 'arg':
      args.append(arg.text)
    if arg.tag == 'ref':
      args.append(device.get_property(arg.text))
  return args

def execute(command_configuration, device):
  command = subprocess.Popen(__construct_args(command_configuration, device), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  print command.communicate()
  print 'result:%s'%command.returncode
