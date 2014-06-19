import os
from os import path
from shutil import copyfileobj, move, rmtree
from multiprocessing.dummy import Pool
from io import IOBase
from hashlib import md5
from datetime import datetime

from PIL import Image

from . import photo_storage
from .application import app
thumb_width = int(app.config['THUMB_WIDTH'])

def md5hex(fd, block_size=2**10):
    dig = md5()
    buf = fd.read(block_size)
    while buf:
        dig.update(buf)
        buf = fd.read(block_size)

    return dig.hexdigest()


def prepare_photo(outdir, thumbdir, fin, filename):
    print('loading', filename, 'to', outdir, 'from', fin)
    fin.seek(0)
    chksum = md5hex(fin)

    impath = path.join(outdir, chksum)
    if path.exists(impath):
        raise IOError("Output file '{0}' already exists".format(impath))

    thumbpath = path.join(thumbdir, chksum)
    if path.exists(thumbpath):
        raise IOError("Thumbnail file '{0}' already exists".format(impath))

    print(filename, 'files ok')

    # Copy image to `outdir`
    fin.seek(0)
    with open(impath, 'wb') as fout:
        copyfileobj(fin, fout)
    print(filename, 'copied')

    # Get date
    fin.seek(0)
    im = Image.open(fin)
    dt = get_exifdate(im)
    print(filename, 'datetime:', dt)

    # Create thumbnail
    print(filename, 'creating thumbnail...')
    try:
        im.thumbnail((thumb_width, thumb_width), Image.ANTIALIAS)
        im.save(thumbpath, 'JPEG')
    except Exception as e:
        print('XXX', e)
        raise e
    print(filename, 'thumbnail saved')

    r = {'chksum': chksum, 'date': dt, 'filename': filename}
    print(filename, '->', r)
    return r

DATETIMEKEY = 0x0132 # copied from PIL.ExifTags
def get_exifdate(im):
    if isinstance(im, (str, IOBase)):
        im = Image.open(im)

    exif = im._getexif()
    if DATETIMEKEY in exif:
        dt = datetime.strptime(exif[DATETIMEKEY], '%Y:%m:%d %H:%M:%S')
    else:
        dt = datetime.utcnow()

    return dt

class UploadSession:
    def __init__(self, sessionid, load=None):
        self.sessionid = sessionid
        self.outdir = path.join(app.config.get('TMPDIR', '/tmp'), sessionid)
        self.thumbdir = path.join(self.outdir, '{0}'.format(thumb_width))

        self.pool = Pool()
        self.images = {}

        if load == 'load':
            self.__load()
        elif load == 'create':
            self.__create()
        elif load is not None:
            raise ValueError('load must be "load", "create" or None')

    def __create(self):
        if path.exists(self.outdir):
            raise IOError('Output directory \'{0}\' exists'.format(self.outdir))
        os.mkdir(self.outdir, 0o0700)
        os.mkdir(self.thumbdir, 0o0700)

    def __load(self):
        if not path.exists(self.outdir) or not path.exists(self.thumbdir):
            raise IOError('Output directory \'{0}\' or \'{1}\' does not exist'.format(self.outdir, self.thumbdir))

        print('loading upload session {0} from {1} ...'.format(self.sessionid, self.outdir))

        for name in os.listdir(self.outdir):
            fp = path.join(self.outdir, name)
            if not path.isfile(fp):
                print('  skipping file \'{0}\''.format(name))
                continue
            print('loading file \'{0}\' to session {1}'.format(name, self.sessionid))
            self.images[name] = {'date': get_exifdate(fp),
                                 'filename': name}

    def get_remote_file(self, fd, filename):
        print('submitting', fd, filename,' to pool')
        self.pool.apply_async(prepare_photo, (self.outdir, self.thumbdir, fd, filename),
                              callback=self.handle_result)

    def finish_uploads(self):
        self.pool.close()
        self.pool.join()

    def handle_result(self, result):
        print('handle_result', result)
        chksum = result.pop('chksum')
        self.images[chksum] = result

    def image_path(self, chksum, thumb):
        if thumb:
            return path.join(self.thumbdir, chksum)
        else:
            return path.join(self.outdir, chksum)

    def dbimport(self, table):
        added = datetime.utcnow()
        for chksum, d in self.images.items():
            date = d['date']
            comment = d['comment']

            move(self.image_path(chksum, False),
                 photo_storage.path(chksum, False))
            move(self.image_path(chksum, True),
                 photo_storage.path(chksum, True))

            table.create(chksum=chksum, date=date, added=added,
                         comment=comment, mimetype='image/jpeg')

    def clear(self):
        if path.exists(self.outdir):
            rmtree(self.outdir)
            self.outdir = None

        if path.exists(self.thumbdir):
            rmtree(self.thumbdir)
            self.thumbdir = None

        self.images.clear()
