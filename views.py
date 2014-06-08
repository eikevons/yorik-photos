from functools import wraps
from flask import render_template, session, redirect, url_for, flash, escape, abort, send_file
from werkzeug import check_password_hash
from peewee import DoesNotExist

from .application import app
from .models import User, Photo
from . import forms
from . import photo_storage

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
    try:
        q = Photo.select().order_by(Photo.date.desc()).limit(1)
        phid = q[0].id
    except Exception:
        abort(500)
    return redirect(url_for('gallery', phid=phid))


@app.route('/gallery')
@app.route('/gallery/<int:phid>')
@app.route('/gallery/<int:phid>/<order>')
@logged_in
def gallery(phid=-1, order='taken'):
    if order not in ('taken', 'added'):
        abort(500)

    if phid >= 0:
        try:
            Photo.get(Photo.id == phid)
        except Photo.DoesNotExist:
            abort(404)

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
        if q.count() >= 1:
            this = q[0]
        if q.count() >= 2:
            old1 = q[1]
        if q.count() >= 3:
            old2 = q[2]
    else:
        for i, p in enumerate(q):
            new1 = new2
            new2 = this
            this = p
            if p.id == phid:
                if i + 1 < q.count():
                    old1 = q[i + 1]
                if i + 2 < q.count():
                    old2 = q[i + 2]
                break
    try:
        with_edit = User.get(User.id == session['userid']).uploader
    except User.DoesNotExist:
        with_edit = False
    print('id: {0} uploader: {1}'.format(session['userid'], with_edit))

    return render_template('gallery.html', new1=new1, new2=new2, this=this, old1=old1, old2=old2, order=order,
                            with_edit=with_edit)


@app.route('/login', methods=('GET', 'POST'))
def login():
    form = forms.LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        try:
            user = User.get(User.name == username)
        except DoesNotExist:
            flash('Unknown username or bad password')
            return render_template('login.html', form=form)

        if check_password_hash(user.password, password):
            flash('Successfully logged in as %s' % escape(username))
            session['userid'] = user.id
            return redirect(url_for('gallery'))
        else:
            flash('Unknown username or bad password YY')
            return render_template('login.html', form=form)

    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.pop('userid', None)
    flash('You were logged out')
    return redirect(url_for('login'))

@app.route('/thumb/<int:phid>')
@logged_in
def thumbnail(phid):
    try:
        photo = Photo.get(Photo.id == phid)
    except DoesNotExist:
        abort(404)

    try:
        path = photo_storage.path(photo.chksum, True)
    except Exception as e:
        print(e)
        raise e
    return send_file(path, mimetype=photo.mimetype)

@app.route('/photo/<int:phid>')
@logged_in
def photo(phid):
    try:
        photo = Photo.get(Photo.id == phid)
    except DoesNotExist:
        abort(404)

    try:
        path = photo_storage.path(photo.chksum, False)
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
        return redirect(url_for('gallery', phid=phid))

    return render_template('edit.html', form=form, p=p)

@app.route('/list')
@app.route('/list/<int:page>')
@logged_in
def list(page=1):
    page_size = 10
    photos = Photo.select().order_by(Photo.date.desc()).paginate(page, page_size)
    print(photos)
    print(photos.count())
    for p in photos:
        print('  ', p.comment)
    return render_template('list.html', page=page, photos=photos, older=(photos.count() == page_size))


