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



from distutils.core import setup
setup(name='traydevice',
  version='1.0',  
  description='Lightweight, highly configurable single device systray representation',
  packages=['traydevice'],
  package_dir={'traydevice':'src/traydevice'},
  package_data={'traydevice':['configuration.xsd','example-configuration.xml']},
  scripts=['scripts/traydevice'],
  author='Martin Špelina',
  author_email='shpelda at seznam dot cz' ,
  license='GPL',
  platforms='any'
  )
