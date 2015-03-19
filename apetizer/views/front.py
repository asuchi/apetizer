'''
Created on 17 mars 2015

@author: rux
'''
from apetizer.views.httpapi import HttpAPIView
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect


class FrontView(HttpAPIView):

    view_name = "front"
    actions = ['home', 'login']

    """
    Display the service home page
    """
    def process_home(self, request, user_profile, input_data, template_args,
                     **kwargs):
        return HttpAPIView.process_view(self,
                                        request, user_profile, input_data,
                                        template_args, **kwargs)

    def process_login(self, request, user_profile, input_data, template_args,
                      **kwargs):
        return HttpAPIView.process_view(self, request,
                                        user_profile, input_data,
                                        template_args, **kwargs)
