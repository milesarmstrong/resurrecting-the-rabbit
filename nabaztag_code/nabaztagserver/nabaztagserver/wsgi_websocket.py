import os
import gevent.monkey
import redis.connection

# This module is used by uWSGI to create the websocket server instance.

redis.connection.socket = gevent.socket
os.environ.update(DJANGO_SETTINGS_MODULE='nabaztagserver.settings')
from ws4redis.uwsgi_runserver import uWSGIWebsocketServer
application = uWSGIWebsocketServer()
