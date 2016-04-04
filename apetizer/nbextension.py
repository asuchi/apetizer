'''
Created on 25 fevr. 2016

@author: biodigitals
'''
from multiprocessing.dummy import DummyProcess
import os
import re
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
    
    def check_origin(self, origin):
        print(origin)
        return True
        return bool(re.match(r'^.*?\.mydomain\.com', origin))
    
    def on_message(self, message):
        pass

    def on_close(self):
        apetizer_core = CoreManager.get_core()
        apetizer_core.wsockets.remove(self)


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
    
    from django.conf import settings
    settings.MEDIA_URL = '/notebooks/medias/'
    
    wsgi_app = tornado.wsgi.WSGIContainer(django.core.handlers.wsgi.WSGIHandler())
    
    # you should add your django app statics to the serveur on config
    #
    # 
    tornado_app = [
      #(r'/static/(.*)', tornado.web.StaticFileHandler, {'path': os.getcwd()+'/static' }),
      (r'/medias/(.*)', tornado.web.StaticFileHandler, {'path': os.getcwd()+'/medias' }),
      (r'/media/(.*)', tornado.web.StaticFileHandler, {'path': os.getcwd()+'/media' }),
      (r"(.+).ws", ApetizerSocket),
      ('.*/query.json$', tornado.web.FallbackHandler, dict(fallback=wsgi_app)),
      ('.*/$', tornado.web.FallbackHandler, dict(fallback=wsgi_app)),
      ]
    web_app.add_handlers(host_pattern, tornado_app)
    
    # start indexing
    from apetizer.directory.items import _search_drilldown_cache
    spawn(_search_drilldown_cache.load_items, tuple(), {})

def spawn(function, fargs, fkwargs):
    """
    Execute the function now in an asynchronous process/thread
    """
    #logger.debug('Spawning execution of %s' % function)
    
    p = DummyProcess(target=function, args=fargs)
    p.start()
    
    return p


    

