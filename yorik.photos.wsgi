import os.path

# NOTE: Modify this to match the deployed version.
basedir = '/home/eike/projects/pivot/ruhebitte2.0'
activate_this = os.path.join(basedir, 'flaskenv/bin/activate_this.py')
execfile(activate_this, dict(__file__=activate_this))

import sys
sys.path.insert(0, basedir)

from ruhebitte import app as application
# NOTE: This has to be the same path as used with
#   WSGIScriptAlias /rb /path/to/ruhebitte.wsgi
# in
#   /etc/apache2/sites-available/ruhebitte.conf
application.config['APPLICATION_ROOT'] = '/rb'

# vim: ft=python
