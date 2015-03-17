'''
Created on 17 mars 2015

@author: rux
'''
import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.context import RequestContext

from apetizer.forms.front import LoginForm
from apetizer.views.httpapi import HttpAPIView
from apetizer.views.actionpipe import ActionPipeView


class FrontView(ActionPipeView):
    
    view_name = "front"
    pipe_name = "login"
    
    actions = ['home','login']
    
    def process_home(self, request, user_profile, input_data, template_args, **kwargs):
        return HttpAPIView.process_view(self, request, user_profile, input_data, template_args, **kwargs)
    
    def process_login(self, request, user_profile, input_data, template_args, **kwargs):
        
        current_user = request.user
        action_data = self.get_actionpipe_data(request)
        
        if not 'pipe_data' in action_data:
            action_data['pipe_data'] = {}
        
        for k in request.POST.keys():
            if not k in ('password','csrfmiddlewaretoken'):
                action_data['pipe_data'][k] = request.POST[k]
        
        action_data =self.update_actionpipe_data(request, action_data)
        
        # validate minimal email form
        if self.validate_action_forms(request, (LoginForm(data=action_data['pipe_data']),)):
            self.save_actionpipe_data(request,action_data)
        
        response = None
        template_args = {}
        template_args['callback_url'] = reverse(self.view_name)
        template_args['current_pipe'] = action_data['pipe']
        
        # if user is not logged in propose him to login or sign up
        if not current_user.is_authenticated():
            
            if 'email' in action_data['pipe_data'] and action_data['pipe_data']['email']:
                
                # is the email in our database ?
                try:
                    email_user = User.objects.get(email=action_data['pipe_data']['email'])
                except:
                    email_user = None
                
                # there is a profile with corresponding email
                if email_user != None:
                    
                    # try to authenticate user if pwd in post
                    if 'password' in request.POST:
                        
                        email_user = authenticate(username=email_user.username,password=request.POST.get('password',None))
                        
                        if email_user is not None:
                            # log the user in
                            if email_user.is_active:
                                login(request, email_user)
                                current_user = email_user
                                return HttpResponseRedirect(reverse('home'))
                            else:
                                # Return a 'disabled account' error message
                                messages.add_message(request, messages.WARNING, _("Your account is disabled. Please contact support for more information or to retrieve it.") )
                        else:
                            # Return an 'invalid login' error message.
                            messages.add_message(request, messages.WARNING, _("Wrong login or password") )
                            
                    # we propose to the user to login
                    template_args['action_forms'] = (LoginForm(initial=action_data['pipe_data']), )
                    template_args['user_exists'] = True
                else:
                    # we continue straight to subscribe
                    response = HttpResponseRedirect(reverse(self.view_name, kwargs={'action':'infos'}))
                
            else:
                template_args['action_forms'] = (LoginForm(initial=action_data['pipe_data']), )
            
            if settings.DEBUG:
                debug_data = action_data['pipe_data']
                template_args['debug_data'] = json.dumps(debug_data)
            
            if not response:
                response = render_to_response('register/login.html', dictionary=template_args, context_instance=RequestContext(request))
        
        
        # if user is logged in retrieve his info and proceed to next view
        else:
            action_data['pipe_data']['first_name'] = current_user.first_name
            action_data['pipe_data']['last_name'] = current_user.last_name
            action_data['pipe_data']['email'] = current_user.email
            if 'password' in request.POST:
                action_data['pipe_data']['password'] = request.POST.get('password', None)
            
            #action_data['pipe_data']['terms_agreed_p'] = user_profile.terms_agreed_p
            
            action_data =self.save_actionpipe_data(request, action_data)
            next_url = self.get_next_url(action_data)
            
            response = HttpResponseRedirect(next_url)
        
        response.set_cookie('akey', action_data['akey'] )
        return response
    