'''
Created on 25 fevr. 2016

@author: biodigitals
'''
import os
import sys

import django.core.handlers.wsgi

from apetizer.manager import CoreManager
from tornado import websocket
import tornado.web
import tornado.wsgi


class ApetizerSocket(websocket.WebSocketHandler):
    
    def open(self, path):
        apetizer_core = CoreManager.get_core()
        apetizer_core.wsockets.append(self)
        #print "WebSocket opened"
    
    def on_message(self, message):
        # post to django app using json data dict ?
        # 
        #print message
        pass
        
    def on_close(self):
        apetizer_core = CoreManager.get_core()
        apetizer_core.wsockets.remove(self)
        #print "WebSocket closed"


def load_jupyter_server_extension(nb_server_app):
    """
    Called when the extension is loaded.

    Args:
        nb_server_app (NotebookWebApplication): handle to the Notebook webserver instance.
    """
    web_app = nb_server_app.web_app
    host_pattern = '.*$'
    
    #
    os.environ.setdefault("APETIZER_PORT", '8888')
    os.environ.setdefault("DJANGO_ENV", 'dev')
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "apetizer.settings")
    
    # add cwd to path
    sys.path.append(os.getcwd())

    django.setup()
    
    wsgi_app = tornado.wsgi.WSGIContainer(django.core.handlers.wsgi.WSGIHandler())
    
    tornado_app = [
      (r'/static/apetizer/(.*)', tornado.web.StaticFileHandler, {'path': os.getcwd()+'/static' }),
      (r'/medias/(.*)', tornado.web.StaticFileHandler, {'path': os.getcwd()+'/medias' }),
      (r'/media/(.*)', tornado.web.StaticFileHandler, {'path': os.getcwd()+'/media' }),
      (r"(.+).ws", ApetizerSocket),
      ('.*/query.json$', tornado.web.FallbackHandler, dict(fallback=wsgi_app)),
      ('.*/$', tornado.web.FallbackHandler, dict(fallback=wsgi_app)),
      ]
    web_app.add_handlers(host_pattern, tornado_app)


