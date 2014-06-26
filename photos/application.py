from flask import Flask

app = Flask('photos')
from . import config
app.config.from_object(config)
