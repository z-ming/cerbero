# mkpkg - CPM packager ,Inspire by Pacman
# Copyright (C) 2017 Mingyi Zhang <mingyi.z@outlook.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

import os
import sys
import re
import tempfile
import platform
import tarfile
import json    

from cerbero.build.cookbook import CookBook
from cerbero.tools.cpm import Pack

class Packager(object):


    def __init__( self, config ,name):
        self.config  = config        
        self.name = name
        self.cookbook = CookBook(self.config)
        self.receipe = self.cookbook.get_recipe(name)
        self.deps = self._deps()


    def _deps(self):
        deps=[]
        runtimes = self.cookbook._runtime_deps()
        
        for receipe in self.cookbook.list_recipe_deps(self.name):
            if self.name == receipe.name or receipe.name in runtimes:
                continue
            deps.append( '%s@%s'%(receipe.name,receipe.version) )

        return deps

    def _mkruntime(self,prefix,output_dir):
        info ={'name':self.name,
               'platform':self.config.platform,
               'arch':self.config.arch,
               'version':self.receipe.version,
               'type':'runtime',
               'prefix':prefix,
               'deps':self.deps }

        items=[]
        for i in self.receipe.dist_files_list():
            path = os.path.join(self.config.prefix,i )
            if os.path.exists(path):
                items.append(i)

        Pack(self.config.prefix,output_dir,info ,items)
        
    def _mkdevel(self,prefix,output_dir):
        info ={'name':self.name,
               'platform':self.config.platform,
               'arch':self.config.arch,
               'version':self.receipe.version,
               'type':'devel',
               'prefix':prefix,
               'deps':self.deps }

        items=[]
        for i in self.receipe.devel_files_list():
            path = os.path.join(self.config.prefix,i )
            if os.path.exists(path):
                items.append(i)

        Pack(self.config.prefix,output_dir,info ,items)

    def make(self,prefix='',output_dir='.'):        
        odir = os.path.abspath( output_dir)
        self._mkruntime(prefix,output_dir)
        self._mkdevel(prefix,output_dir)

        #generate runtime
