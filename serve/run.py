'''
run.py
runs the server as a wsgi process; meant to be called by gunicorn
'''
from werkzeug.contrib.fixers import ProxyFix
from meduele_server import *

app.wsgi_app = ProxyFix(app.wsgi_app)
