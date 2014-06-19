#!/usr/bin/env python3
import sys
from functools import wraps
from datetime import datetime

import arrow
from werkzeug import generate_password_hash

from photos.models import db, User, Photo

def connected(f):
    """Simple decorator to assure db connection"""
    @wraps(f)
    def wrapped(*args, **kwargs):
        if db.is_closed():
            db.connect()
        return f(*args, **kwargs)
    return wrapped


@connected
def create_tables():
    print('Creating User table')
    User.create_table()
    print('Creating Photo table')
    Photo.create_table()

@connected
def test_init():
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
def list_users():
    tmpl = '{id:<3}  {name:<20}  {email:<30}  {uploader:^8}'

    head = tmpl.format(id='Id', name='Name', email='Email', uploader='Uploader')

    print(head)
    print('-' * len(head))
    for u in User.select().dicts():
        print(tmpl.format(**u))

@connected
def list_photos():
    tmpl1 = '{id:<3}  {chksum:<32}  {date:<26}'
    tmpl2 = '         {comment:<30}  {added:<26}'

    desc = dict(id='Id', chksum='Checksum', date='Date', comment='Comment', added='Added')

    head1 = tmpl1.format(**desc)
    head2 = tmpl2.format(**desc)
    print(head1)
    print(head2)
    print('-' * max(len(head1), len(head2)))


    for p in Photo.select().dicts():
        print(tmpl1.format(**p))
        print(tmpl2.format(**p))

@connected
def test_create():
    create_tables()
    test_init()

def run_app():
    from photos import app
    app.run()

def main():
    arg2func = {
            'create': create_tables,
            'tcreate': test_create,
            'users': list_users,
            'photos': list_photos,
            'test' : test_init,
            'run' : run_app
            }
    if len(sys.argv) == 2 and sys.argv[1] in arg2func:
        arg2func[sys.argv[1]]()
    else:
        sys.exit('''Usage: {0} COMMAND

Possible COMMANDs:
{1}'''.format(sys.argv[0], ' '.join(arg2func)))

if __name__ == "__main__":
    main()
