#!/usr/bin/env python3
import sys
from functools import wraps
from datetime import datetime

import arrow
from werkzeug import generate_password_hash

from photos.models import db, User, Photo
from photos.upload import UploadSession

def connected(f):
    """Simple decorator to assure db connection"""
    @wraps(f)
    def wrapped(*args, **kwargs):
        if db.is_closed():
            db.connect()
        return f(*args, **kwargs)
    return wrapped


@connected
def create_tables(args):
    print('Creating User table')
    User.create_table()
    print('Creating Photo table')
    Photo.create_table()

@connected
def test_init(args):
    users = [('viewer 1', 'viewer_1@example.com', 'pass1', False),
             ('viewer 2', 'viewer_2@example.com', 'pass2', False),
             ('uploader 1', 'uploader1@example.com', 'uppass1', True),
             ('uploader 2', 'uploader2@example.com', 'uppass2', True)]

    photos = [('111', '2014-06-07T20:21:19', 'photo 111'),
              ('12345', '2014-06-05T20:21:19', 'photo 12345'),
              ('222', '2014-06-04T20:21:19', 'photo 222'),
              ('333', '2014-06-07T22:21:19', 'photo 333'),
              ('444', '2014-06-05T20:21:19', '444'),
              ('555', '2014-06-01T20:21:19', 'photo 555'),
              ('666', '2014-06-05T14:21:19', 'photo 666'),
              ('abcde', '2014-05-02T20:21:19', 'photo abcde'),
              ('uvw', '2014-03-02T20:21:19', 'photo uvw'),
              ('xyz', '2014-07-02T20:21:19', 'photo xyz'),
              ]


    if User.select().count() == 0:
        for n, e, p, u in users:
            User.create(name=n, email=e, password=generate_password_hash(p), uploader=u)
    else:
        print('User table already contains data')

    str2datetime = lambda s: arrow.get(s).datetime.replace(tzinfo=None)

    if Photo.select().count() == 0:
        for s, d, c in photos:
            kw = dict(chksum=s, date=str2datetime(d), comment=c,
                    added=datetime.utcnow(),
                    mimetype='image/jpeg')
            print(kw)
            Photo.create(**kw)
    else:
        print('Photo table already contains data')


@connected
def list_users(args):
    tmpl = '{id:<3}  {name:<20}  {email:<30}  {uploader:^8}'

    head = tmpl.format(id='Id', name='Name', email='Email', uploader='Uploader')

    print(head)
    print('-' * len(head))
    for u in User.select().dicts():
        print(tmpl.format(**u))

@connected
def list_photos(args):
    tmpl1 = '{id:<3}  {chksum:<32}  {date}'
    tmpl2 = '         {comment:<30}  {added}'

    desc = dict(id='Id', chksum='Checksum', date='Date', comment='Comment', added='Added')

    head1 = tmpl1.format(**desc)
    head2 = tmpl2.format(**desc)
    print(head1)
    print(head2)
    print('-' * (max(len(head1), len(head2))  + 12))


    for p in Photo.select().dicts():
        print(tmpl1.format(**p))
        print(tmpl2.format(**p))

@connected
def test_create(args):
    create_tables()
    test_init()

def run_app(args):
    from photos import app
    app.run()

@connected
def adduser(args):
    if len(args) == 2:
        name, password = args
        email = None
        uploader = None
    elif len(args) == 3:
        name, password, email = args
        uploader = None
    elif len(args) == 4:
        name, password, email, uploader = args
    else:
        sys.exit('''adduser requires 2 to 4 arguments:
  adduser NAME PASSWORD [EMAIL [UPLOADER]]''')

    kwargs = {'name': name,
              'password': generate_password_hash(password),
              'email' : email or '',
              'uploader': bool(uploader)}

    print('Adding user \'{0}\''.format(name))
    for k, v in sorted(kwargs.items()):
        if k == 'name':
            continue
        print('{0:<9} {1}'.format(k + ':', v))

    correct = input('Data correct? [yes/NO] ')
    if correct.lower() == 'yes':
        User.create(**kwargs)
        print('Added', name)
    else:
        print('Aborting.')

@connected
def addphoto(args):
    if len(args) == 2:
        path, comment = args
    else:
        sys.exit('''addphoto requires 2 arguments:
  addphoto PATH COMMENT''')

    us = UploadSession('console-{0:%s}'.format(datetime.utcnow()), 'create')

    with open(path, 'rb') as image:
        us.get_remote_file(image, path)
        us.finish_uploads()
        chksum = tuple(us.images.keys())[0]
        us.images[chksum]['comment'] = comment
        us.dbimport(Photo)
        us.clear()

    print('Added \'{0}\' with chksum={1} and comment \'{2}\''.format(path, chksum, comment))



def main():
    arg2func = {
            'create': create_tables,
            'tcreate': test_create,
            'users': list_users,
            'photos': list_photos,
            'test' : test_init,
            'run' : run_app,
            'adduser' : adduser,
            'addphoto' : addphoto
            }
    if len(sys.argv) >= 2 and sys.argv[1] in arg2func:
        arg2func[sys.argv[1]](sys.argv[2:])
    else:
        sys.exit('''Usage: {0} COMMAND

Possible COMMANDs:
{1}'''.format(sys.argv[0], ' '.join(sorted(arg2func))))

if __name__ == "__main__":
    main()
