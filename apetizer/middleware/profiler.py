'''
Created on 11 dec. 2015

@author: biodigitals
'''
import sys

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from django.conf import settings


class CProfileMiddleware(object):
    def process_view(self, request, callback, callback_args, callback_kwargs):
        if settings.DEBUG and 'profile' in request.GET:
            import cProfile
            self.profiler = cProfile.Profile()
            args = (request,) + callback_args
            return self.profiler.runcall(callback, *args, **callback_kwargs)

    def process_response(self, request, response):
        if settings.DEBUG and 'profile' in request.GET and hasattr(self, 'profiler'):
            import pstats
            self.profiler.create_stats()
            out = StringIO()
            old_stdout, sys.stdout = sys.stdout, out
            #pstats.Stats(self.profiler).sort_stats('time', 'calls').print_stats()
            pstats.Stats(self.profiler).sort_stats(request.GET.get('sortstats', 'cumulative')).print_stats()
            sys.stdout = old_stdout
            response.content = '<pre>%s</pre>' % out.getvalue()
        return response
