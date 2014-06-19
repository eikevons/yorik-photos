from os.path import join, exists
from hashlib import sha256
from subprocess import check_call

from .application import app

class StorageError(Exception):
    pass

def path(chksum, thumb):
    if thumb:
        parts = (app.config['PHOTO_STORAGE'], 'thumbs-{0}'.format(app.config['THUMB_WIDTH']), '{0}'.format(chksum))
    else:
        parts = (app.config['PHOTO_STORAGE'], '{0}'.format(chksum))
    return join(*parts)

def get_photo(chksum):
    return open(path(chksum, False))

def get_thumbnail(chksum):
    return open(path(chksum, True))

def store_photo(data):
    chksum = sha256(data).hexdigest()

    p = path(chksum, False)
    t = path(chksum, False)
    if exists(p) or exists(t):
        raise StorageError('Photo with chksum {0} already uploaded!'.format(chksum))

    with open(p, 'w') as of:
        of.write(data)

    check_call(['convert', '-resize', app.config['THUMB_WIDTH'], p, t])
