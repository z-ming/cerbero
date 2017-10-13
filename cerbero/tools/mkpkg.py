# mkpkg - Python packager ,Inspire by Pacman
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

def to_unixpath(path):
    if path[1] == ':':
        path = '/%s%s' % (path[0], path[2:])
    return path

def _varpath(path, prefix,vname='${prefix}'):
    '''
    calc the varpath corresponding self.prefix
    '''
    var=os.path.normpath(path).replace('\\','/')
    assert os.path.isabs(path)
    assert os.path.isabs(prefix)

    #all to unix path
    uprefix = to_unixpath(prefix).replace('\\','/')
    upath   = to_unixpath(var)
    rpath = os.path.relpath(upath.lower(),uprefix.lower())
    n = len(upath)-len(rpath)
    if rpath == '.' or n ==0:
        return vname
        
    if rpath.startswith("..") or n < 0 :
        return None
    return vname +'/' + upath[n:]
def _rpath(path,prefix):
    x = _varpath(path,prefix,'')
    if x.startswith('/'):
        x = x[1:]
    return x

def _readlines(f):
    lines=f.readlines()
    for i in range(len(lines)):
        lines[i] =lines[i].rstrip('\r\n')
    return lines

def _writelines(f,lines):
    for i in lines:
        f.write(i.rstrip('\r\n')+'\n')




class FileNormalizer(object):

    def __init__(self,arcname,prefix):
        self._archive_name = arcname
        self._prefix = prefix


    def normalize(self, path ):
        if path.endswith('.pc') or path.endswith('.la'):
            d = os.path.dirname(path)
            if not os.path.exists(d):
                os.makedirs(d)
            f = open(path,'w')
            if path.endswith('.pc'):
                self._pc_normalize(f)
            elif path.endswith('.la'):
                self._la_normalize(f)
            f.close()
            return True
        return False

    def _relpath(self,path):
        '''
        calc the varpath corresponding self.prefix
        '''
        var=os.path.normpath(path).replace('\\','/')
        if os.path.isabs(path):
            #all to unix path
            uprefix = to_unixpath(self._prefix).replace('\\','/')
            upath   = to_unixpath(var)
            rpath = os.path.relpath(upath.lower(),uprefix.lower())
            n = len(upath)-len(rpath)
            if rpath == '.' or n ==0:
                return '${prefix}'
            
            if rpath.startswith("..") or n < 0 :
                return None

            return '${prefix}/' + upath[n:]
        return var




    def _pc_normalize(self, f):
        path = os.path.join(self._prefix,self._archive_name)
        lines = _readlines(open(path,'r'))

        vars ={}#'key','value','lineno'
        flags={}
        P = re.compile(r'^(?P<key>\w+)=(?P<value>.+)')
        n =0
        prefix = None
        for n in range(len(lines)):
            line = lines[n]
            m = P.match( line )
            if not m:
                continue
            vars[ m.group('key')]={ 'lineno':n,
                'value':m.group('value')}

            if m.group('key') == 'prefix':
                prefix = m.group('value')

        assert vars.has_key('prefix'),'''
        No prefix in the pc (%s)
        '''%path

        FLAG_P = re.compile(r'^(?P<key>Libs\.private?):(?P<value>.+)')
        n =0
        for n in range(len(lines)):
            line = lines[n]
            m = FLAG_P.match( line )
            if not m:
                continue
            flags[ m.group('key')]={ 'lineno':n,
                'value':m.group('value')}

        #assert prefix.startswith(self._prefix),'''
        #prefix : %s
        #prefix : %s
        #'''%(prefix,self._prefix)


        toNorm=[] #var to be normalize
        prefixVars=[]

        for key, value in vars.viewitems():
            if key == 'prefix':
                continue

            _VALUE=re.compile(r'^\$\{(?P<name>\w+)\}.*')
            m = _VALUE.match( value['value'] )
            if m:
                if m.group('name')=='prefix':
                    prefixVars.append(key)
                continue
            toNorm.append(key)
        
        for i in toNorm:
            name   = i
            value  = vars[i]['value']
            lineno = vars[i]['lineno']
            lines[lineno]='%s=%s '%(name,self._relpath(value))

        for i in prefixVars:
            name   = i
            value  = vars[i]['value']
            lineno = vars[i]['lineno']

            rpath = _rpath(prefix,self._prefix)#os.path.relpath(prefix,self._prefix)
            if rpath == '.' or rpath == '':
                continue
            lineno=vars[i]['lineno']
            print '+',rpath
            value ='${prefix}/%s'%rpath + value[len('${prefix}/'):] + ' '
            print '[+]',value
            lines[lineno]='%s=%s'%(name,value)

        #Libs and Libs.private
        for key in ['Libs.private']:
            flag = flags.get(key,None)
            if flag == None:
                continue
            value  = flag['value']
            lineno = flag['lineno']
            line=''
            for field in value.split():
                if field.startswith('-L'):
                    d = field[2:]
                    if d.startswith('${'):
                        continue
                    rpath = _rpath( d , self._prefix )
                    line +=' -L${prefix}/'+rpath
                else:
                    line +=' %s'%field
            lines[lineno] = '%s:%s'%(key,line)
        prefix = self._prefix.replace('\\','/')
        if platform.system()=="Windows" and prefix.startswith('/'):
            prefix ='%s:%s'%(prefix[1],prefix[2:])
        lines[ vars['prefix']['lineno']] ='prefix=%s'%prefix

        _writelines(f, lines)


    def _la_normalize(self,f):
        path = os.path.join(self._prefix,self._archive_name)
        lines = _readlines(open(path,'r'))
        P = re.compile(r"^(?P<key>(libdir|dependency_libs))=\'(?P<value>.+)\'")
        for i in range(len(lines)):
            line = lines[i]
            m = P.match(line)
            if not m :
                continue

            if m.group('key')=='libdir':
                val =self._relpath(m.group('value'))
                lines[i] = "libdir='%s'"%val
                

            if m.group('key')=='dependency_libs':
                items =m.group('value').split()
                vars={}

                for val in items:
                    flag=''
                    if val[0] == '-':
                        flag= val[:2]
                        val = val[2:]

                    if not vars.has_key(flag):
                        vars[flag]=set()

                    if flag in ['','-L','-R']:
                        d = self._relpath( val.lstrip('=') )
                        vars[flag].add( d )
                    else:
                        vars[flag].add(val)
                val =''

                for flag ,items in vars.viewitems():
                    for it in items:
                        val += '%s%s '%(flag,it)
                lines[i]="dependency_libs=' %s '"%val 
        _writelines(f,lines)


class Packager(object):
    """Packager """
    def __init__(self,name, version,platform,arch,pkg_type,ext='tar.bz2',prefix=''): 
        """Packager constructor.
        
        Args:
            name: name of the package which to be packed.
            version: version of the package.
            prefix: prefix of files stored 
        """
        self._name = name
        self._version = version
        self._platform = platform
        self._arch = arch
        self._prefix = prefix
        self._type = pkg_type
        self._ext = ext
        self._rootd = os.path.abspath(os.getcwd())
        self._info={}
        self._output_dir=os.path.abspath(os.getcwd())
        self._files=[]
        self._norfiles={}
        self._desc={'name':self._name,
        'version': self._version,
        'type':self._type,
        'deps':[]
        }

        self._tmpdir=None
        self._force = False
    
    def set_pkg_src_dir(self, d ):
        self._rootd = d
    

    
    def set_output_dir(self, d):
        self._output_dir = os.path.realpath( d )

    def filename(self):
        """filename of the pcakge"""
        t={'runtime':'','devel':'-devel'}[self._type]
        return "%s%s-%s-%s-%s%s.%s" % (self._prefix, self._name,
                self._platform, self._arch,
                self._version, t,self._ext)

    def _addfile(self,rpath):
        if not os.path.exists( os.path.join(self._rootd, rpath)):
            print '%s not exists!'%rpath
            assert not self._force,'''
            request file : %s not exists
            '''%rpath
            return
        self._files.append(rpath)




    def _add(self,path):
        """ add file or directory to the package
        
        Args:
            path: file or dir to be added
        """
        if os.path.isabs( path ):
            rpath = _rpath( path,self._rootd)
            assert rpath is not None

            if os.path.isdir( path ):
                self._add_directory(rpath)
            else:
                self._addfile(rpath)
        else:
            p = os.path.join(self._rootd,path)
            if os.path.isdir(p):
                self._add_directory( p)
            else:
                self._addfile(path)


    def add(self,paths):
        if type(paths) == type([]):
            for path in paths:
                self._add( path )
        else:
            path = paths
            self._add(path)


    def _add_directory(self,rdir):
        d = os.path.join(self._rootd, rdir)

        for dirpath,dirnames,filenames in os.walk(d):
            rpath = _rpath(dirpath,self._rootd)
            assert rpath is not None
            for filename in filenames:
                self._files.append('%s/%s'%(rpath,filename))

    def _tmp_dir(self):
        if self._tmpdir is None:
            import tempfile
            self._tmpdir = tempfile.mkdtemp()
        return self._tmpdir


    def _preprocess(self):
        for filename in self._files:
            if filename.endswith('.pc'):
                pc = FileNormalizer( filename,self._rootd)
                path = os.path.join( self._tmp_dir(),'pc',filename)
                pc.normalize( path )
                self._norfiles[filename]=path

            elif filename.endswith('.la'):
                la = FileNormalizer( filename,self._rootd)
                path = os.path.join( self._tmp_dir(),'la',filename)
                la.normalize( path )
                self._norfiles[filename]=path
            else:
                path = os.path.join( self._rootd, filename)

    def _gen_desc(self):
        path = os.path.join( self._tmp_dir(),'.desc')
        f = open(path,'w')

        json.dump(self._desc,f, indent =2 )

        f.close()
        return path


    def pack(self):
        """
        package files
        """
        path = os.path.join(self._output_dir,self.filename())
        assert not os.path.exists(path),'''
        the package %s already exists
        '''%path

        self._preprocess()

        tar = tarfile.open(path, "w:bz2")
        for filename in self._files:
            path = os.path.join(self._rootd,filename)
            if self._norfiles.has_key(filename):
                path = self._norfiles[filename]
            #    tar.add(path,filename)

            tar.add(path,filename)
        tar.add( self._gen_desc(),'.desc')    
        tar.close()

    def depend(self,name,version):
        """
        add a dependent
        """
        self._desc['deps'].append('%s@%s'%(name,version))

def _wopen(path,mod='wb'):
    if mod.startswith('w'):
        d = os.path.dirname(path)
        if os.path.exists(d):
            os.makedirs(d)
    return open(path,mod)

def _freplace(filename,prefix):
    f = openfile
class Tar:

    def __init__(self,path,mod):
        self._tar = tarfile.open(path,mod)

    

    def close(self):
        self._tar.close()

    def add(item, )    
def Install(prefix, path):
    ''' inatall package to 'prefix' directory '''
    tar = tarfile.open(path,"r:bz2")
    content = f.read()
    desc = json.loads(content,encoding='utf-8')

    typ = {'runtime':'','devel':'-devel'}[desc['type']]
    instd =os.path.join(prefix,'%(name)s@%(version)s-%(type)s'%desc) )
    if not os.path.exists(instd):
        os.makedirs( instd)
    tar.extract('.desc',instd)

    f = open( os.path.join(instd,'files'),'w' )
    for i in tar:
        if i.name == '.desc':
            continue
        tar.extract(i,prefix)

    f.write(content)
    f.close()


    instd = os.path.join(prefix,'.inst')
    if not os.path.exists(instd):
        os.makedirs(instd)




    tar.close()

if __name__ == '__main__':
    ''' Command  '''
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("--name", type=str,
                    help="Name of the package to be packed")

    parser.add_argument("--version", type=str,
                    help="Version of the package to be packed")

    parser.add_argument("--platform", type=str, choices=["windows","linux",'auto'],
                    default='auto',
                    help="Platform of the package to be packed")

    parser.add_argument("--arch", type=str, choices=["x86","x86_64",'auto'],
                    default='auto',
                    help="Architecture of the package to be packed")

    parser.add_argument("--type", type=str, choices=["runtime","devel"],
                    default='runtime',
                    help="Type of the package to be packed")

    parser.add_argument("--root-dir", type=str, 
                    help="Source root directory of the package to be packed")


    parser.add_argument("--prefix", type=str, default='',
                    help="Prefix of the package to be packed")

    parser.add_argument("--output-dir", type=str, default='.',
                    help="Output directory of the package to be packed")
    args = parser.parse_args()

    if args.platform == 'auto':
        args.platform = platform.system().lower()

    pkg = Packager( args.name, args.version,args.platform,args.arch,args.type,
    prefix = args.prefix )

    d = os.path.abspath(args.root_dir)

    pkg.set_pkg_src_dir( d )

    pkg.set_output_dir(args.output_dir)

    pkg.add(d)
    pkg.pack()
