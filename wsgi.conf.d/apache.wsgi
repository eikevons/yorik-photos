import sys
from site import addsitedir
from os.path import join

# NOTE: Modify this to match the deployed version.
venvbase = '/var/local/yorik-photos'
sitepkg = join(venvbase, 'lib/python3.4/site-packages')
appbase = join(venvbase, 'yorik-photos')

# Make venv availale
addsitedir(sitepkg)

sys.path.insert(0, appbase)

from photos import app as application
# NOTE: This has to be the same path as used with
#   WSGIScriptAlias /yorik /var/local/yorik-photos/yorik-photos/wsgi.conf.d/apache.wsgi
# in
#   /etc/apache2/sites-available/yorik-photos.conf
application.config['APPLICATION_ROOT'] = '/yorik'

# vim: ft=python
