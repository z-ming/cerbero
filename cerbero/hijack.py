
import platform
import os
import shutil
import cerbero

from cerbero.utils import shell, _, fix_winpath, to_unixpath, git
from cerbero.utils import messages as m

#load auto config
cac={'cerbero':cerbero}
CERBERO_AUTO_CONFIG=None

if not os.path.exists('cerbero.cac'):
    CERBERO_AUTO_CONFIG=os.getenv('CERBERO_AUTO_CONFIG',None)
    if CERBERO_AUTO_CONFIG is not None:
        if os.path.exists( CERBERO_AUTO_CONFIG):
            shutil.copy(CERBERO_AUTO_CONFIG,'cerbero.cac')
        else:            
            shell.download(CERBERO_AUTO_CONFIG,'cerbero.cac')

if os.path.exists('cerbero.cac'):
    import cerbero
    path = os.path.abspath('cerbero.cac')
    print 'Loading',path


    execfile(path,cac)



if platform.system() == 'Windows':
    #import cerbero.bootstrap.build_tools
    #import cerbero.bootstrap.hijack.build_tools
    #cerbero.bootstrap.build_tools.BuildTools = \
    #cerbero.bootstrap.hijack.build_tools.BuildTools

    #overwrite windows bootstrap with hijack one
    import cerbero.bootstrap.bootstrapper
    import cerbero.bootstrap.hijack.windows
    cerbero.bootstrap.hijack.windows.register_all()

    import cerbero.build.build
    import cerbero.build.hijack.cmake
    cerbero.build.build.BuildType.AUTOCMAKE= \
    cerbero.build.hijack.cmake.AutoCMake



_old_shell_download = shell.download

if cac.get('mirror',None):

    def _hijack_download(url, destination=None, recursive=False, check_cert=True, overwrite=False):
        check_cert = False
        mirror_url = cac['mirror'](url)
        if mirror_url:
            m.message('%s has been redirect to %s.'%(url,mirror_url))
            _old_shell_download( mirror_url,destination,recursive,check_cert,overwrite)
        else:
            _old_shell_download( url,destination,recursive,check_cert,overwrite)
    shell.download = _hijack_download