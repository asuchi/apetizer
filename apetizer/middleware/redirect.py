'''
Created on 5 fevr. 2013

@author: rux
'''
from multiprocessing.process import Process

from django.core.exceptions import ObjectDoesNotExist
from django.http.response import HttpResponsePermanentRedirect, Http404

from apetizer.models import Item, Translation, object_tree_cache, AuditedModel


REDRIRECT_URL_PATTERNS = []

class ItemRedirect(object):
    """
    Middleware to handle item url redirects
    """
    def process_request(self, request):
        
        # bypass the redirect for the staff users
        if request.user and request.user.is_staff:
            return
        
        try:
            if not 'domain' in request.__dict__:
                request.domain = request.META['HTTP_HOST'].split(':')[0]
            
            node_path = '/'+request.domain+request.path
            item = Item.objects.get_at_url(node_path, exact=True)
        except ObjectDoesNotExist:
            return
        
        if item and item.redirect_url and (item.published == True or item.visible == False):
            return HttpResponsePermanentRedirect(item.redirect_url)


    def process_response(self, request, response):
        
        # dispacth caching
        object_tree_cache.purge()
        
        # dispatch indexing
        
        return response

        