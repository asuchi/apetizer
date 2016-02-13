#!/usr/bin/env python

# Run this with
# PYTHONPATH=. DJANGO_SETTINGS_MODULE=testsite.settings testsite/tornado_main.py
# Serves by default at
# http://localhost:8080/hello-tornado and
# http://localhost:8080/hello-django

import json
import os

from apetizer.dispatchers.async import AsyncDispatcher
from apetizer.manager import CoreManager

import django.core.handlers.wsgi

from tornado import websocket
import tornado.httpserver
import tornado.ioloop
from tornado.options import options, define, parse_command_line
import tornado.web
import tornado.wsgi

os.environ.setdefault("APETIZER_PORT", '8000')

os.environ.setdefault("DJANGO_ENV", 'dev')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "apetizer.settings")

if django.VERSION[1] > 5:
    django.setup()

define('port', type=int, default=int(os.environ['APETIZER_PORT']))


class ClientSocket(websocket.WebSocketHandler):
    
    def open(self, path):
        apetizer_core = CoreManager.get_core()
        apetizer_core.wsockets.append(self)
        print "WebSocket opened"
    
    def on_message(self, message):
        # post to django app using json data dict ?
        # 
        print message
        
    def on_close(self):
        apetizer_core = CoreManager.get_core()
        apetizer_core.wsockets.remove(self)
        print "WebSocket closed"


class Announcer(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        
        message = self.get_argument('data')
        
        data = {}
        data['subject'] = 'Pushed'
        data['message'] = message
        
        apetizer_core = CoreManager.get_core()
        
        for socket in apetizer_core.wsockets:
            socket.write_message(json.dumps(data))
        
        self.write('Posted')


def main():
    parse_command_line()

    wsgi_app = tornado.wsgi.WSGIContainer(django.core.handlers.wsgi.WSGIHandler())

    tornado_app = tornado.web.Application(
    [
      (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': 'static' }),
      (r"/push", Announcer),
      (r"(.+).ws", ClientSocket),
      ('.*', tornado.web.FallbackHandler, dict(fallback=wsgi_app)),
      ])

    server = tornado.httpserver.HTTPServer(tornado_app)
    server.listen(options.port)

    dispatcher = AsyncDispatcher.get_instance()
    dispatcher.start()

    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
    
