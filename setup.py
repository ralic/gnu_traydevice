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
from distutils.command.install_data import install_data as install_data
from distutils.command.install_lib import install_lib as install_lib
from distutils.command.install import install as _install
from distutils.core import setup
from distutils.core import Command
from distutils.errors import DistutilsFileError
from distutils.command.build_py import build_py
import subprocess
import shutil
import os
import fileinput
import glob
import sys
from os.path import *
sys.path.insert(0, join(dirname(__file__), 'src'))
import traydevice
import pydoc
import re

class package_ini(Command):
    """
        Locate 'package.ini' in all installed packages and patch it as
        requested by wildcard references to install process.
    """
    user_options = []

    def initialize_options(self):
        self.packages = None
        self.version = None

    def finalize_options(self):
        self.set_undefined_options(build_py.__name__,
                                   ('packages', 'packages'))
        self.version = self.distribution.get_version()

    def visit(self, dirname, names):
        if basename(dirname) in self.packages:
            if 'package.ini' in names:
                self.patch(join(dirname, 'package.ini'))

    def patch(self, ini_file):
        print 'patching file' + ini_file
        with open(ini_file, 'r') as infile:
            file_data = infile.readlines()
        with open(ini_file, 'w') as outfile:
            for line in file_data:
                _line = self.patch_line(line)
                if _line:
                    line = _line
                outfile.write(line)

    def patch_line(self, line):
        """
            Patch an installed package.ini with setup's variables
        """
        match = re.match("""
            (?P<identifier>\w+)\s*=.*\#\#SETUP_PATCH
                \\((?P<command>.*)\.(?P<variable>.*)\\)""", line, re.VERBOSE)
        if not match:
            return line
        print 'Replacing:' + line
        line = match.group('identifier')
        line += ' = '
        data = '(self).distribution.get_command_obj(\'' + \
                match.group('command') + '\')' + '.' + \
                match.group('variable')
        line += '\'' + str(eval(data)) + '\''
        line += '\n'
        print 'With:' + line
        return line

    def run(self):
        """
            Patch package.ini files in distribution package
            with variables from setup
        """
        walk(
            self.distribution.get_command_obj(install.__name__).install_lib,
            package_ini.visit,
            self)


class install_manpage(install_data):
    """Install manpages that are already built in build directory"""
    user_options = []

    def initialize_options(self):
        install_data.initialize_options(self)
        self.build_base = None
        self.data_files = []

    def finalize_options(self):
        self.set_undefined_options('install',
                                   ('install_man', 'install_dir'),
                                   ('build_base', 'build_base'),
                                  )
        for mantype in xrange(1, 9):
            manpages = glob.glob('build/man/*.%i' % mantype)
            if manpages:
                self.data_files += [('man%i' % mantype, manpages)]


class install(_install):
    sub_commands = _install.sub_commands + [
           (package_ini.__name__, None),
           (install_manpage.__name__, None)]

    user_options = _install.user_options + [
        ('install-man=', None, "directory for Unix man pages")]

    def initialize_options(self):
        _install.initialize_options(self)
        self.install_man = 'man'

    def finalize_options(self):
        _install.finalize_options(self)
        self.convert_paths('man')
        if self.root is not None:
            self.change_roots('man')
        self.install_man = os.path.join(self.install_base, self.install_man)


class build_manpage(Command):
    """Create a manpages from docbook source"""

    user_options = []

    def initialize_options(self):
        self.build_base = None#location of build dir

    def finalize_options(self):
        self.set_undefined_options('build',
                                   ('build_base', 'build_base'))

    def man(self, input_file):
        source = join(
            dirname(__file__), input_file)
        man_dir = join(self.build_base, 'man')
        if not exists(man_dir):
            os.makedirs(man_dir)
        exe = subprocess.Popen(
            ["docbook2man", abspath(source)], cwd=man_dir)
        exe.communicate()
        if exe.returncode != 0:
            raise DistutilsFileError(source)

    def run(self):
        doc_dir = join(
            dirname(__file__), 'doc')
        for source in glob.glob(join(doc_dir, '*.xml')):
            self.man(source)


class build(_build):
    """Make build process call build_manpage command"""

    sub_commands = _build.sub_commands + [
        (build_manpage.__name__, None)]

    def __init__(self, dist):
        _build.__init__(self, dist)


docs = pydoc.splitdoc(traydevice.__doc__)

setup(
    cmdclass={build.__name__: build,
              build_manpage.__name__: build_manpage,
              install_manpage.__name__: install_manpage,
              install_data.__name__: install_data,
              install_lib.__name__: install_lib,
              install.__name__: install,
              package_ini.__name__: package_ini},
    name=traydevice.__name__,
    version='devel',
    description=docs[0],
    long_description=docs[1],
    packages=[traydevice.__name__],
    package_dir={traydevice.__name__: 'src/traydevice'},
    package_data={traydevice.__name__: ['package.ini']},
    data_files=[('', glob.glob('data/*')),
                ('', ['README.txt']),
                ('', ['LICENSE.txt'])],
    scripts=glob.glob('scripts/*'),
    author='Martin Špelina',
    author_email='shpelda at seznam dot cz',
    license='GPL',
    url='https://savannah.nongnu.org/projects/traydevice/',
    platforms='linux')
