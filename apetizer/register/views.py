'''
Created on 3 fevr. 2015

@author: nicolas
'''
from collections import OrderedDict
import json
import random
import string

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _

from apetizer.register.forms import LoginInfosForm, RegisterInfosForm, \
    RegisterCompleteForm, RegisterOrLoginForm, RegisterLoginForm
from apetizer.views.actionpipe import ActionPipeView


class RegisterView(ActionPipeView):
    
    pipe_name = 'register'
    view_name = 'register'
    
    view_template = 'register/view.html'
    
    actions = ['lost', 'login', 'logout', 'infos', 'complete']
    
    actions_forms = {'login':(LoginInfosForm,),
                    'infos':(LoginInfosForm, RegisterInfosForm),
                    'complete':(RegisterCompleteForm,)}
    
    action_templates = {'login':'register/login.html',
                        'infos':'register/infos.html',
                        'complete':'register/complete.html',}
    
    
    def __init__(self, **kwargs):
        
        self.pipe_scenario = OrderedDict([
                # Check email to see if user known.
                ('email', {'class':self.__class__, 'action':'login'}),
                ('first_name', {'class':self.__class__, 'action':'infos'}),
                ('last_name', {'class':self.__class__, 'action':'infos'}),
                ('user_registred', {'class':self.__class__, 'action':'end'}),
                ])
        
        
    def process_view(self, request, user_profile, input_data, template_args, **kwargs):
        
        return ActionPipeView.process_view(self, request, user_profile, input_data, template_args, **kwargs)
        
    def process_lost(self, request, user_profile, input_data, template_args, **kwargs):
        
        return ActionPipeView.process_view(self, request, user_profile, input_data, template_args, **kwargs)
    
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
        if self.validate_action_forms(request, (RegisterOrLoginForm(data=action_data['pipe_data']),)):
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
                    template_args['action_forms'] = (RegisterLoginForm(initial=action_data['pipe_data']), )
                    template_args['user_exists'] = True
                else:
                    # we continue straight to subscribe
                    response = HttpResponseRedirect(reverse(self.view_name, kwargs={'action':'infos'}))
                
            else:
                template_args['action_forms'] = (RegisterOrLoginForm(initial=action_data['pipe_data']), )
            
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
    
    
    def process_logout(self, request, user_profile, input_data, template_args, **kwargs):
        logout(request)
        return HttpResponseRedirect(reverse('home'))
    
    """
    Basic view for owner registration. This should only be used if user is logged out.
    If user is logged in, actionpipe should take him to RegisterProfileCompleteView
    """
    def process_infos(self, request, user_profile, input_data, template_args, **kwargs):
        
        action_data = self.get_actionpipe_data(request)

        # check if user has logged in inbetween
        if request.user.is_authenticated():
            return HttpResponseRedirect(reverse(self.view_name, kwargs={'action':'complete'}))

        if not 'pipe_data' in action_data:
            action_data['pipe_data'] = {}
            
        # filter posted data and update
        action_data['pipe_data'] = self.update_data_with_post(request, action_data['pipe_data'], self.get_action_forms('infos'))
        
        # overwrite paswword with encrypted one
        for k in request.POST.keys():
            if k == 'Zpassword':
                # encrypt password as soon as we get it for security
                action_data['pipe_data'][k] = make_password(request.POST[k])
        
        action_data =self.update_actionpipe_data(request, action_data)
        
        # fill forms
        template_args['action_forms'] = self.get_validated_forms(tuple(), action_data['pipe_data'], kwargs.get('action',self.default_action), save_forms=False)
        
        #template_args['action_forms'] = (LoginInfosForm(data=action_data['pipe_data']), RegisterInfosForm(data=action_data['pipe_data']))
        
        # check for form validity
        all_forms_valid = self.validate_action_forms(request, template_args['action_forms'])
        
        # check if user email exists
        if all_forms_valid and 'email' in action_data['pipe_data'] and action_data['pipe_data']['email']:
            # is the email in our database ?
            try:
                email_user = User.objects.get(email=action_data['pipe_data']['email'])
            except:
                email_user = None
            
            # there is a profile with corresponding email
            if email_user != None:
                
                # we redirect to the user login
                if request.user.is_authenticated():
                    return HttpResponseRedirect( reverse( self.view_name, kwargs={'action':'complete'} ) )
                else:
                    # set message to the user that we found it's email
                    messages.add_message(request, messages.SUCCESS, _("Looks like you already have an account!") )
                    # this occurs when the users changes it's email to a know one on the profil info page
                    # so we save the data
                    self.save_actionpipe_data(request, action_data)
                    return HttpResponseRedirect( reverse( self.view_name, kwargs={'action':'login'} ) )
        
        if all_forms_valid:
            self.save_actionpipe_data(request, action_data)
        
        next_url = self.get_next_url(action_data)
        if next_url == request.path or request.method.lower() == 'GET'.lower() or all_forms_valid == False:
            
            if settings.DEBUG:
                debug_data = {}
                for key in action_data:
                    debug_data[key] = str(action_data[key])
                template_args['debug_data'] = json.dumps(debug_data)
            if settings.DEBUG:
                response = self.finish( request, self.render(request, template_args, action_data, **kwargs), user_data=action_data, **kwargs)
            else:
                response = self.finish( request, self.render(request, template_args, {}, **kwargs), user_data=action_data, **kwargs)
        else:
            response = HttpResponseRedirect(next_url)
        
        return response

    
    """
    View where we ask a logged in user to complete his profile info in order to do the action he is trying to do.
    """
    def process_complete(self, request, user_profile, input_data, template_args, **kwargs):
        
        # check if user is not authenticated and should register or login first
        if not request.user.is_authenticated():
            return HttpResponseRedirect(reverse(self.view_name, kwargs={'action':'login'}))
        
        action_data = self.get_actionpipe_data(request)
        
        if not 'pipe_data' in action_data:
            action_data['pipe_data'] = {}
        
        # filter posted data and update
        action_data['pipe_data'] = self.update_data_with_post(request, action_data['pipe_data'], self.actions_forms['complete'])
        
        action_data =self.update_actionpipe_data(request, action_data)
        
        # assign template data
        template_args['action_forms'] = self.get_validated_forms(tuple(), action_data['pipe_data'], kwargs.get('action',self.default_action), save_forms=False)
        template_args['pipe_data'] = action_data
        
        # finally, check for forms validity
        all_forms_valid = self.validate_action_forms(request, template_args['action_forms'])
        if all_forms_valid:
            self.save_actionpipe_data(request, action_data)
        
        next_url = self.get_next_url(action_data)
        if next_url == request.path or request.method == 'GET' or all_forms_valid == False:
            
            if settings.DEBUG:
                debug_data = {}
                for key in action_data:
                    debug_data[key] = str(action_data[key])
                template_args['debug_data'] = json.dumps(debug_data)
            
            response = self.finish( request, self.render(request, template_args, action_data), user_data=action_data, **kwargs)
        else:
            response = HttpResponseRedirect(next_url)
        
        return response



    
    def finish_action_pipe(self, request):
        
        action_data = self.get_actionpipe_data(request)

        user = request.user
        profile_data = action_data['pipe_data']

        if user.is_authenticated():
            
            # update pipe data with user data
            action_data['pipe_data']['first_name'] = user.first_name
            action_data['pipe_data']['last_name'] = user.last_name
            action_data['pipe_data']['email'] = user.email
            
            # Mark user as registered to continue the actionpipe
            action_data['pipe_data']['user_registered'] = True
            action_data =self.update_actionpipe_data(request, action_data)
            action_data =self.save_actionpipe_data(request, action_data)
            
            # continue actionpipe
            next_url = self.get_next_url(action_data)
            if next_url == request.path:
                return HttpResponseRedirect(reverse('home'))
            else:
                return HttpResponseRedirect(next_url)
        
        # clean user data for user creation.
        first_name = profile_data['first_name']
        username = slugify(first_name).replace('-', '')[:25]
        username += '-' + ''.join(random.choice(string.ascii_uppercase+string.digits) for _ in range(4))
        
        User.objects.create_user(username, profile_data['email'], profile_data['password'])
        
        new_user = authenticate(username=username, password=profile_data['password'])
        login(request, new_user)
        
        # mark user as registered to continue the actionpipe
        # and update action data
        action_data['pipe_data']['user_registered'] = True
        action_data =self.update_actionpipe_data(request, action_data)
        action_data =self.save_actionpipe_data(request, action_data)
        
        # continue actionpipe
        if action_data['pipe'] == self.pipe_name:
            return HttpResponseRedirect(reverse('home'))
        else:
            return HttpResponseRedirect(self.get_next_url(action_data))



