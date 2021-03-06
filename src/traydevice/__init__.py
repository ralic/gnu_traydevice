# -*- coding: utf-8 -*-
#Copyright (C) 2009  Martin Špelina <shpelda at gmail dot com>
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
"""Lightweight,highly configurable single device systray representation

Traydevice is a little systray application allowing you to conveniently execute
configured commands on the specified device.
"""
import os
inipath = os.path.join(os.path.dirname(__file__), 'package.ini')
with open(inipath) as ini:
    for line in ini.readlines():
        exec(line)
