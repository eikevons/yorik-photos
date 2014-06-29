##
## Copyright (c) 2014 Jan Eike von Seggern
##

from functools import wraps
from math import ceil
from flask import render_template, session, redirect, url_for, flash, escape, abort, send_file, request, jsonify, send_from_directory
from werkzeug import check_password_hash
from time import time

from .application import app
from .models import User, Photo
from . import forms
from . import photo_storage
from .upload import UploadSession


def logged_in(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if 'userid' not in session:
            flash('Du bist nicht angemeldet!')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapped


@app.route('/')
@logged_in
def index():
    return redirect(url_for('timeline'))

def safe_index(l, i, default=None):
    try:
        return l[i]
    except IndexError:
        return default

def last_item(iterable, default=None):
    for default in iterable:
        pass
    return default

def is_uploader(uid=None):
    if uid is None:
        uid = session['userid']
    try:
        return User.get(User.id == uid).uploader
    except User.DoesNotExist:
        return False

@app.route('/timeline')
@app.route('/timeline/<int:phid>')
@app.route('/timeline/<int:phid>/<order>')
@logged_in
def timeline(phid=-1, order='taken'):
    if order not in ('taken', 'added'):
        abort(500)

    if phid >= 0:
        try:
            Photo.get(Photo.id == phid)
        except Photo.DoesNotExist:
            abort(404)

    first = None
    last = None
    new1 = None
    new2 = None
    this = None
    old1 = None
    old2 = None

    if order == 'taken':
        q = Photo.select().order_by(Photo.date.desc())
    else:
        q = Photo.select().order_by(Photo.added.desc())

    if phid < 0:
        this = safe_index(q, 0)
        old1 = safe_index(q, 1)
        old2 = safe_index(q, 2)
        if old2 != None:
            last = last_item(q)
            if last == old2:
                last = None
    else:
        # save the iterator to a variable to make sure we do not loop more
        # than we need to
        enum = enumerate(q)
        for i, p in enum:
            if first is None:
                first = p
            new2 = new1
            new1 = this
            this = p
            if p.id == phid:
                old1 = safe_index(q, i+1)
                old2 = safe_index(q, i+2)
                break
        last = last_item(enum, (None, None))[1]
        if first == new1:
            first = None

    return render_template('timeline.html',
                           new1=new1, new2=new2,
                           this=this,
                           old1=old1, old2=old2,
                           first=first, last=last,
                           order=order,
                           photoid=this.id,
                           uploader=is_uploader())

@app.route('/gallery')
@app.route('/gallery/<order>')
def gallery(order='taken'):
    if order == 'taken':
        photos = Photo.select().order_by(Photo.date.desc())
    else:
        photos = Photo.select().order_by(Photo.added.desc())

    return render_template('gallery.html', photos=photos, uploader=is_uploader(), order=order)



@app.route('/login', methods=('GET', 'POST'))
def login():
    form = forms.LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        try:
            user = User.get(User.name == username)
        except User.DoesNotExist:
            flash('Unknown username or bad password')
            return render_template('login.html', form=form)

        if check_password_hash(user.password, password):
            flash('Successfully logged in as %s' % escape(username))
            session['userid'] = user.id
            return redirect(url_for('timeline'))
        else:
            flash('Unknown username or bad password YY')
            return render_template('login.html', form=form)

    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.pop('userid', None)
    flash('You were logged out')
    return redirect(url_for('login'))

@app.route('/photo/<int:phid>')
@app.route('/photo/<int:phid>/<size>')
@logged_in
def photo(phid, size='normal'):
    try:
        photo = Photo.get(Photo.id == phid)
    except Photo.DoesNotExist:
        abort(404)

    try:
        path = photo_storage.path(photo.chksum, size.lower() == 'small')
    except Exception as e:
        print(e)
        raise e
    return send_file(path, mimetype=photo.mimetype)

@app.route('/edit/<int:phid>', methods=('GET', 'POST'))
@logged_in
def edit(phid):
    try:
        u = User.get(User.id == session['userid'])
    except User.DoesNotExist:
        abort(500)

    if not u.uploader:
        abort(403)

    try:
        p = Photo.get(Photo.id == phid)
    except Photo.DoesNotExist:
        abort(500)

    form = forms.EditForm(recorded=p.date, comment=p.comment)
    if form.validate_on_submit():
        p.date = form.recorded.data
        p.comment = form.comment.data
        p.save()
        return redirect(url_for('timeline', phid=phid))

    return render_template('edit.html', photoid=p.id, form=form, p=p)

@app.route('/list')
@app.route('/list/<int:page>')
@logged_in
def list(page=1):
    page_size = 10

    photos = Photo.select().order_by(Photo.date.asc())
    page_max = ceil(photos.count() / page_size)

    if page < page_max - 1:
        first_page = page_max
    else:
        first_page = None

    return render_template('list.html',
                           page=page,
                           photos=photos.paginate(page, page_size),
                           newer=(page < page_max),
                           first_page=first_page,
                           uploader=is_uploader())


@app.route('/upload', methods=('GET', 'POST'))
@logged_in
def upload():
    if not is_uploader():
        abort(403)

    if request.method == 'GET':
        return render_template('upload.html')

    # POST request
    print('POSTing to upload')
    try:
        session_id = session['upload_session']
        us = UploadSession(session_id, 'load')
    except KeyError as e:
        print('no upload session:', e)
        abort(500)
    print('POSTing to upload: {0}'.format(session_id))

    for chksum, comment in request.form.items():
        if chksum not in us.images:
            print('chksum \'{0}\' missing in session'.format(chksum))
            abort(501)
        us.images[chksum]['comment'] = comment
        print('  ', us.images[chksum])
    us.dbimport(Photo)
    us.clear()

    return redirect(url_for('list'))


@app.route('/_upload_images', methods=('GET', 'POST'))
def upload_images():
    session_id = '{0}::{1}'.format(session['userid'], time())
    session['upload_session'] = session_id
    us = UploadSession(session_id, 'create')
    for f in request.files.getlist('files[]'):
        us.get_remote_file(f, f.filename)
    us.finish_uploads()
    images = [{'chksum': chksum,
               'date': im['date'].strftime('%d.%m.%Y %H:%M:%S')}
               for chksum, im in us.images.items()]
    ret = {'session': session_id, 'images': images}
    print('XX', ret)
    return jsonify(**ret)

@app.route('/preview/<chksum>')
def preview(chksum):
    print('preview', chksum)
    try:
        session_id = session['upload_session']
    except KeyError:
        abort(403)
    print('preview', session_id)

    us = UploadSession(session_id)
    return send_from_directory(us.thumbdir, chksum, mimetype='image/jpeg')
