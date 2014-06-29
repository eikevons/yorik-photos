##
## Copyright (c) 2014 Jan Eike von Seggern
##

from flask import Flask

app = Flask(__name__)
from . import config
app.config.from_object(config)
