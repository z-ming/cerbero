# cerbero - a multi-platform build system for Open Source software
# Copyright (C) 2012 Andoni Morales Alastruey <ylatuya@gmail.com>
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


#from cerbero.oven import Oven
from cerbero.commands import Command, register_command
from cerbero.build.cookbook import CookBook
from cerbero.build.oven import Oven
from cerbero.utils import _, N_, ArgparseArgument
from cerbero.tools.mkpkg import Packager, BuildTree

class MKPkg(Command):
    doc = N_('Make package for modules')
    name = 'mkpkg'

    def __init__(self, force=None, no_deps=None):
            args = [
                ArgparseArgument('module', nargs='*',
                    help=_('name of the modules to make')),

                ArgparseArgument('--type', type=str,
                    default='receipe',choices=['receipe','package','sdk','build-tools'],
                    help=_('type of the moudle')),
                    
                ArgparseArgument('--prefix', type=str,
                    default='',
                    help=_('prefix of package file name')),

                ArgparseArgument('--output-dir', type=str,
                    default='.',
                    help=_('directory of package to be output')),

                ArgparseArgument('--missing-files', action='store_true',
                    default=False,
                    help=_('prints a list of files installed that are '
                           'listed in the recipe')),
                ArgparseArgument('--dry-run', action='store_true',
                    default=False,
                    help=_('only print commands instead of running them '))]
            if force is None:
                args.append(
                    ArgparseArgument('--force', action='store_true',
                        default=False,
                        help=_('force the build of the recipe ingoring '
                                    'its cached state')))
            if no_deps is None:
                args.append(
                    ArgparseArgument('--no-deps', action='store_true',
                        default=False,
                        help=_('do not build dependencies')))

            self.force = force
            self.no_deps = no_deps
            Command.__init__(self, args)

    def run(self, config, args):
        if args.type == 'build-tools':
            self._build_tools( config ,args )
            return



        bt = BuildTree(config)
        receipes = args.module
        if args.type == 'package':
            all=[]
            for i in receipes:
                all +=bt.receipes(i)
            receipes = all


        elif args.type == 'sdk':
            print 'SDK not support ,for now.'
            return

        for name in receipes:
            pkg = Packager(config,name)
            pkg.make( args.prefix,args.output_dir)

    def _build_tools(self, config, args):
        bt = BuildTree(config)
        pkg = bt.package('gstreamer-1.0')
        print config.build_tools_prefix
        assert pkg.sdk_version == '1.0'
        
        
        info ={'name':'build-tools',
        'platform':config.platform,
        'arch':config.arch,
        'version':pkg.version,
        'type':'runtime',
        'prefix':args.prefix,
        'deps':[] }

        from cerbero.tools.cpm import Pack


        Pack(config.build_tools_prefix,args.output_dir,info )
   


register_command(MKPkg)
