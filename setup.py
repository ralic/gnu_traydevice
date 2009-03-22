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
from distutils.command.install_data import install_data
from distutils.command.install import install as _install
from distutils.core import setup
from distutils.core import Command
from distutils.errors import DistutilsFileError
from distutils.command.build_py import build_py
import subprocess
import shutil
import os
from glob import glob
import sys
from os.path import *
sys.path.insert(0, join(dirname(__file__), 'src'))
import traydevice
import pydoc
import re


def patch_file(patch_line, file_to_patch):
    """
        Modifies a file in place applying 'patch_line' function
        to each line of the file
    """
    print 'patching file:' + file_to_patch
    with open(file_to_patch, 'r') as infile:
        file_data = infile.readlines()
    with open(file_to_patch, 'w') as outfile:
        for line in file_data:
            _line = patch_line(line)
            if _line:
                line = _line
            outfile.write(line)


class package_ini(Command):
    """
        Locate 'package.ini' in all installed packages and patch it as
        requested by wildcard references to install process.
    """
    user_options = []

    def initialize_options(self):
        self.packages = None
        self.install_lib = None
        self.version = None

    def finalize_options(self):
        self.set_undefined_options(build_py.__name__,
                                   ('packages', 'packages'))
        self.set_undefined_options(install.__name__,
                                   ('install_lib', 'install_lib'))
        self.version = self.distribution.get_version()

    def visit(self, dirname, names):
        if basename(dirname) in self.packages:
            if 'package.ini' in names:
                patch_file(self.patch_line, join(dirname, 'package.ini'))

    def patch_line(self, line):
        """
            Patch an installed package.ini with setup's variables
        """
        match = re.match("""
            (?P<identifier>\w+)\s*=.*\#\#SETUP_PATCH
                \\((?P<command>.*)\.(?P<variable>.*)\\)""", line, re.VERBOSE)
        if not match:
            return line
        print 'Replacing:' + line.replace('\n','')
        line = match.group('identifier')
        line += ' = '
        data = '(self).distribution.get_command_obj(\'' + \
                match.group('command') + '\')' + '.' + \
                match.group('variable')
        line += '\'' + str(eval(data)) + '\''
        line += '\n'
        print 'With:' + line.replace('\n','')
        return line

    def run(self):
        """
            Patch package.ini files in distribution package
            with variables from setup
        """
        walk(
            self.install_lib,
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
            manpages = glob(join(self.build_base, 'man') +
                                    '/*.%i' % mantype)
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
    """
        Create a manpages from docbook source
    """

    user_options = []

    def initialize_options(self):
        self.build_base = None
        self.data_dir = None

    def finalize_options(self):
        self.set_undefined_options('build',
                                   ('build_base', 'build_base'))
        self.set_undefined_options('install_data',
                                   ('install_dir', 'data_dir'))

    def man(self, input_file):
        """Create a manpage from docbook source file"""
        source = join(
            dirname(__file__), input_file)
        man_tmp_dir = join(self.build_base, 'man_tmp')
        man_dir = join(self.build_base, 'man')
        for directory in [man_tmp_dir, man_dir]:
            if not exists(directory):
                os.makedirs(directory)
        shutil.copy(source, man_tmp_dir)
        patched_file = join(man_tmp_dir, basename(source))
        patch_file(self.patch_line, patched_file)
        exe = subprocess.Popen(
            ["docbook2man", abspath(patched_file)], cwd=man_dir)
        exe.communicate()
        if exe.returncode != 0:
            raise DistutilsFileError(source)

    def patch_line(self, line):
        return line.replace('@XSD_PATH@',
                    join(self.data_dir, 'configuration.xsd'))

    def run(self):
        doc_dir = join(
            dirname(__file__), 'doc')
        for source in glob(join(doc_dir, '*.xml')):
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
              install.__name__: install,
              package_ini.__name__: package_ini},
    name=traydevice.__name__,
    version='devel',
    description=docs[0],
    long_description=docs[1],
    packages=[traydevice.__name__],
    package_dir={traydevice.__name__: 'src/traydevice'},
    package_data={traydevice.__name__: ['package.ini']},
    data_files=[('', glob('data/*')),
                ('', ['README.txt']),
                ('', ['LICENSE.txt'])],
    scripts=glob('scripts/*'),
    author='Martin Špelina',
    author_email='shpelda at seznam dot cz',
    license='GPL',
    url='https://savannah.nongnu.org/projects/traydevice/',
    platforms='linux')
