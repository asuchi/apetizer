'''
Created on 17 mars 2015

@author: rux
'''

from django.contrib.auth import logout
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect

from apetizer.views.front import FrontView
from apetizer.views.httpapi import HttpAPIView


class DashboardView(HttpAPIView):
    
    view_name = "dashboard"
    
    actions = ['logout',]
    
    def pre_process(self, request, user_profile, input_data, **kwargs):
        
        if not request.user.is_authenticated():
            return HttpResponseRedirect(reverse(FrontView.view_name, kwargs={'action':'login'}))
        
        return HttpAPIView.pre_process(self, request, user_profile, input_data, **kwargs)
        
    def process_view(self, request, user_profile, input_data, template_args, **kwargs):
        return HttpAPIView.process_view(self, request, user_profile, input_data, template_args, **kwargs)
    
    def process_logout(self, request, user_profile, input_data, template_args, **kwargs):
        logout(request)
        return HttpResponseRedirect('/')

