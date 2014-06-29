##
## Copyright (c) 2014 Jan Eike von Seggern
##

from flask import Flask

app = Flask('photos')
from . import config
app.config.from_object(config)
