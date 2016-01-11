'''
Created on 5 fevr. 2013

@author: rux
'''
from django.core.exceptions import ObjectDoesNotExist
from django.http.response import HttpResponsePermanentRedirect

from apetizer.models import Item


REDRIRECT_URL_PATTERNS = []

class ItemRedirect(object):
    """
    Middleware to handle item url redirects
    """
    def process_request(self, request):
        
        # check if redirection is active
        #if not settings.CONTENT_DO_REDIRECT:
        #    return
        
        # bypass the redirect for the staff users
        if request.user and request.user.is_staff:
            return
        
        try:
            node_path = '/'+request.META['HTTP_HOST'].split(':')[0]+request.path
            item = Item.objects.get_at_url(node_path, exact=True)
        except ObjectDoesNotExist:
            return
        
        if item and item.redirect_url and (item.published == True or item.visible == False):
            return HttpResponsePermanentRedirect(item.redirect_url)


    