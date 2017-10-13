
import platform
import os
import shutil
from cerbero.utils import shell, _, fix_winpath, to_unixpath, git
from cerbero.utils import messages as m

#load auto config
cac=None
CERBERO_AUTO_CONFIG=None

if not os.path.exists('cerbero.cac'):
    CERBERO_AUTO_CONFIG=os.getenv('CERBERO_AUTO_CONFIG',None)
    if CERBERO_AUTO_CONFIG is not None:
        if os.path.exists( CERBERO_AUTO_CONFIG):
            shutil.copy(CERBERO_AUTO_CONFIG,'cerbero.cac')
        else:            
            shell.download(CERBERO_AUTO_CONFIG,'cerbero.cac')
print os.path.exists('cerbero.cac')
if os.path.exists('cerbero.cac'):
    import cerbero
    d={}
    cac =execfile('./cerbero.cac',d)
    print d
    print hasattr(d,'mirror')
    print '**********',cac



if platform.system() == 'Windows':
    #overwrite windows bootstrap with hijack one
    import cerbero.bootstrap.bootstrapper
    import cerbero.bootstrap.hijack.windows
    cerbero.bootstrap.hijack.windows.register_all()


_old_shell_download = shell.download
print cac,hasattr(cac,'mirror'),'@@@'

if cac and hasattr(cac,'mirror'):
    def _hijack_download(url, destination=None, recursive=False, check_cert=True, overwrite=False):
        mirror_url = cac.mirror(url)
        if mirror_url:
            m.message('%s has been redirect to %s.'%(url,mirror_url))
            _old_shell_download( mirror_url,destination,recursive,check_cert,overwrite)
        else:
            _old_shell_download( url,destination,recursive,check_cert,overwrite)
    shell.download = _hijack_download