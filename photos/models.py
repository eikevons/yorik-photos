from peewee import *
from flask import g

from .application import app

db = SqliteDatabase(app.config['DATABASE'])

# register DB connection with flask app
@app.before_request
def establish_connection():
    g.db = db
    g.db.connect()

@app.after_request
def close_connection(response):
    g.db.close()
    return response


class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    id = PrimaryKeyField()
    name = CharField()
    email = CharField()
    password = CharField()
    uploader = BooleanField(default=False)

class Photo(BaseModel):
    id = PrimaryKeyField()
    chksum = CharField()
    mimetype = CharField()
    date = DateTimeField()
    added = DateTimeField()
    comment = TextField()
