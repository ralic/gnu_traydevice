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
#from distutils.command.install_data import install_data as _install_data
from distutils.core import setup
from distutils.core import Command
from distutils.errors import DistutilsFileError
import subprocess
import shutil
import os
import fileinput
import glob


#class install_data(_install_data):
#    """
#      Install hook
#    """
#
#    def run(self):
#        self.replace_wildcards()
#        _install_data.run(self)
#
#    def replace_wildcards(self):
#        """ Patch generated manpages so that they'll contain
#            correct file references
#        """
#        print self.install_dir
#        pass
#
#
class build(_build):
    """Make build process call manpage command"""

    sub_commands = _build.sub_commands + [
        ('manpage', None)
    ]

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

    def man(self, input_file):
        source = os.path.join(
            os.path.dirname(__file__), input_file)
        man_dir = os.path.join(self.build_base, 'man')
        if not os.path.exists(man_dir):
            os.makedirs(man_dir)
        exe = subprocess.Popen(
            ["docbook2man", os.path.abspath(source)], cwd=man_dir)
        exe.communicate()
        if exe.returncode != 0:
            raise DistutilsFileError(source)

    def run(self):
        doc_dir = os.path.join(
            os.path.dirname(__file__), 'doc')
        for source in glob.glob(os.path.join(doc_dir, '*.xml')):
            self.man(source)


import sys
import os.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
import traydevice
import pydoc


docs = pydoc.splitdoc(traydevice.__doc__)

manpage_data_files = []
for mantype in xrange(1, 9):
    manpages = glob.glob('build/man/*.%i' % mantype)
    if manpages:
        manpage_data_files += [('share/man/man%i' % mantype, manpages)]

setup(
    cmdclass={'build': build,
              'manpage': manpage},
#              'install_data': install_data},
    name=traydevice.__name__,
    version=traydevice.__version__,
    description=docs[0],
    long_description=docs[1],
    packages=[traydevice.__name__],
    package_dir={traydevice.__name__: 'src/traydevice'},
    data_files=manpage_data_files + [
                ('share/' + traydevice.__name__, glob.glob('data/*')),
                ('share/' + traydevice.__name__, ['README.txt']),
                ('share/' + traydevice.__name__, ['LICENSE.txt'])
               ],
    scripts=glob.glob('scripts/*'),
    author='Martin Špelina',
    author_email='shpelda at seznam dot cz',
    license='GPL',
    url='https://savannah.nongnu.org/projects/traydevice/',
    platforms='linux')
