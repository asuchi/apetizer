'''
Created on 3 fevr. 2015

@author: nicolas
'''
from collections import OrderedDict

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from apetizer.forms.register import AuthenticateLoginForm, AuthenticatePasswordForm, \
   RegisterForm, AuthenticateAgreeForm, UserForm
from apetizer.models import Visitor
from apetizer.views.visitor import VisitorView


class UserView(VisitorView):
    """
    Login and registration management class
    """
    view_name = 'authenticate'
    view_template = 'register/view.html'
    class_actions = ['register', 'login', 'logout',]
    
    class_actions_forms = {'login': (AuthenticateLoginForm,),
                           'register': (UserForm, 
                                        AuthenticatePasswordForm, 
                                        AuthenticateAgreeForm),
                           }
    
    class_action_templates = {'register': 'register/register.html',
                              'login': 'register/login.html',
                              }
    
    def __init__(self, *args, **kwargs):
        super(UserView, self).__init__(*args, **kwargs)
        main_scenario = OrderedDict([
                                          ('username',
                                           {'class': self.__class__,
                                            'action': 'profile'}),
                                          ('email',
                                           {'class': self.__class__,
                                            'action': 'profile'}),
                                          ('first_name',
                                           {'class': self.__class__,
                                            'action': 'register'}),
                                          ('last_name',
                                           {'class': self.__class__,
                                            'action': 'register'}),
                                          ('password',
                                           {'class': self.__class__,
                                            'action': 'register'}),
                                          ('validated',
                                           {'class': self.__class__,
                                            'action': 'validate'}),
                                          ])
        
        self.action_scenarios['register'] = main_scenario
        #self.action_scenarios['login'] = main_scenario
        
    def get_forms_instances(self, action, user_profile, kwargs):
        
        if action in UserView.class_actions:
            if self.request.user.is_authenticated():
                return (self.request.user,)
            else:
                # prefill the user model with user_profile data
                user = get_user_model()()
                user.email = kwargs['pipe']['data'].get('email', user_profile.email)
                user.username = kwargs['pipe']['data'].get('username', user_profile.username)
                user.first_name = kwargs['pipe']['data'].get('first_name')
                user.last_name = kwargs['pipe']['data'].get('last_name')
                return (user,)
        else:
            return super(UserView, self).get_forms_instances(action, user_profile, kwargs)
        
    
    def pre_process(self, request, input_data, **kwargs):
        # ensure password is not saved in the pipe
        if 'password' in input_data and input_data['password']:
            input_data['password'] = 'XXXXXXXX'
        return super(UserView, self).pre_process(request, input_data, **kwargs)

    def process_login(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Propose to the visitor to log in
        """
        if user_profile.username:
            kwargs['pipe']['data']['username'] = user_profile.username
        
        if 'username' in request.POST \
            and 'password' in request.POST:
            
            # what is the user name ?
            user = authenticate(username=request.POST.get('username',None),
                                password=request.POST.get('password',None))
            
            if user is not None:
                login(request, user)
                
                #
                user_profile.email = user.email
                user_profile.username = user.username
                user_profile.validated = now()
                user_profile.save()
                
                # redirect
                return HttpResponseRedirect(user_profile.get_url()+'next/')
            else:
                # Return an 'invalid login' error message.
                messages.add_message(request, messages.WARNING, _("Wrong login or password"))
        
        return self.manage_pipe(request, user_profile, input_data, template_args, **kwargs)
        


    def process_logout(self, request, user_profile, input_data, template_args, **kwargs):
        logout(request)
        # rotate akey also
        return self.process_reset(request, user_profile, input_data, template_args, **kwargs)


    def process_register(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Set a password for the current user
        """
        # profile must have username and email
        if not user_profile.email:
            return HttpResponseRedirect(user_profile.get_url()+'profile/')
        
        if not user_profile.validated:
            return HttpResponseRedirect(user_profile.get_url()+'profile/')
        
        #return self.manage_pipe(request, user_profile, input_data, template_args, **kwargs)
        # is ther a user logged in ?
        if request.user.is_authenticated():
            # the user should be able to set it's password
            # ask him the current one to change to a anew one
            return self.manage_pipe(request, user_profile, input_data, template_args, **kwargs)
        else:
            # check for forms validity
            #kwargs['pipe']['data']['username'] = user_profile.username
            #kwargs['pipe']['data']['email'] = user_profile.email
        
            # check for an existing user
            try:
                user = get_user_model().objects.get(username=user_profile.username)
                messages.add_message(request, messages.WARNING, _("A user with this username already exists"))
                return HttpResponseRedirect(user_profile.get_url()+'login/')
            except ObjectDoesNotExist:
                # create a user
                # set user password
                if 'password' in request.POST and request.POST['password']:
                    user, = self.get_forms_instances(kwargs['action'], user_profile, kwargs)
                    #print 'SETTING PWD'
                    user.set_password(request.POST['password'])
                    user.save()
                    
                    # log the user in
                    auth_user = authenticate(username=user.username,
                                            password=request.POST['password'])
                    login(request, auth_user)
                    
                    user_profile.username = auth_user.username
                    user_profile.email = auth_user.email
                    user_profile.save()
            
            return self.manage_pipe(request, user_profile, input_data, template_args, **kwargs)
        


