'''
Created on 22 sept. 2015

@author: biodigitals
'''
from django.conf import settings
from django.http.response import HttpResponseRedirect

from apetizer.views.action import ActionView
from apetizer.views.api import ApiView
from apetizer.models import get_new_uuid
from apetizer.manager import CoreManager
from apetizer.dispatchers.async import AsyncDispatcher


class BusynessView(ApiView, ActionView):
    """
    When a node is flagged busy, 
    there should be an operation running 
    witch modifies it's content and/or children content
    during witch editing of the item is forbidden
    """
    view_name = 'status'

    class_actions = ['status']
    class_action_templates = {
                              'status':'apetizer/status.html',
                              }
    
    def process(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Look upon the current content node if it's busy 
        and redirect to the status page if it is ...
        """
        action = kwargs.get('action',BusynessView.default_action)
        if not action in ['status']:
            # check for current node busy status
            if template_args['currentNode'].is_busy and settings.DEBUG == False:
                # if node is busy, show the status page
                return HttpResponseRedirect(self.get_reversed_action(self.view_name, 'status', kwargs))
        
        # detach thread upon too busy job ...
        return super(BusynessView, self).process(request, user_profile, input_data, template_args, **kwargs)

    def process_status(self, request, user_profile, input_data, template_args, **kwargs):
        # check for page busy status
        # ask data from running job ?
        return self.render(request, template_args, input_data, **kwargs)
    
    
    def start_job(self, pipe, func, args, kwargs):
        # generate a processing key based on akey
        key = get_new_uuid()
        
        core = CoreManager.get_core()
        core.jobs[key] = AsyncDispatcher.get_instance().spawn(func, args, kwargs)
        
        return key

    def stop_job(self, key):
        pass



