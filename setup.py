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
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

from distutils.command.build import build as _build
from distutils.core import setup
from distutils.core import Command
from distutils.errors import DistutilsFileError
import subprocess
import shutil
import os
import fileinput


class build(_build):
    """Make build process call manpage command"""

    sub_commands = _build.sub_commands + [('manpage', None)]

    def __init__(self, dist):
        _build.__init__(self, dist)


class manpage(Command):
    """Create a manpages from docbook source"""

    user_options = []

    def initialize_options(self):
        #location of build dir
        self.build_base = self.distribution.get_command_obj('build').build_base
        pass

    def finalize_options(self):
        pass

    def run(self):
        print self.build_base
        man_1_dir = os.path.join(self.build_base, 'share/man/man1')
        man_5_dir = os.path.join(self.build_base, 'share/man/man5')
        manpage_1_source = os.path.join(
            os.path.dirname(__file__), 'doc/traydevice.xml')
        manpage_5_source = os.path.join(
            os.path.dirname(__file__), 'doc/traydevice-config.xml')
        shutil.rmtree(man_1_dir, ignore_errors=True)
        shutil.rmtree(man_5_dir, ignore_errors=True)
        os.makedirs(man_1_dir)
        os.makedirs(man_5_dir)
        exe = subprocess.Popen(
            ["docbook2man", os.path.abspath(manpage_1_source)], cwd=man_1_dir)
        exe.communicate()
        if exe.returncode != 0:
            raise DistutilsFileError(manpage_1_source)
        exe = subprocess.Popen(
            ["docbook2man", os.path.abspath(manpage_5_source)], cwd=man_5_dir)
        exe.communicate()
        if exe.returncode != 0:
            raise DistutilsFileError(manpage_5_source)

import sys
import os.path
sys.path.insert(0,os.path.join(os.path.dirname(__file__), 'src'))
import traydevice

setup(cmdclass={'build': build, 'manpage': manpage},
    name='traydevice',
    version=traydevice.__version__,
    description="""Lightweight,
        highly configurable single device systray representation""",
    long_description="""Traydevice is a little desktop application
        displaying systray icon allowing you to conveniently execute
        custom commands on the specified defice.""",
    packages=['traydevice'],
    package_dir={'traydevice': 'src/traydevice'},
    package_data={'traydevice':
        ['configuration.xsd', 'example-configuration.xml']},
    data_files=[('share/man/man1', ['build/share/man/man1/traydevice.1'])],
    scripts=['scripts/traydevice'],
    author='Martin Špelina',
    author_email='shpelda at seznam dot cz',
    license='GPL',
    url='https://savannah.nongnu.org/projects/traydevice/',
    platforms='linux')
