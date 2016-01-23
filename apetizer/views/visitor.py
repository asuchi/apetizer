'''
Created on 8 oct. 2015

@author: biodigitals
'''
from collections import OrderedDict
import json

from django.conf import settings
from django.forms.models import model_to_dict
from django.http import HttpResponseRedirect
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _, get_language

from apetizer.dispatchers.async import AsyncDispatcher
from apetizer.forms.register import VisitorValidateForm, VisitorForm
from apetizer.models import Visitor
from apetizer.parsers.json import API_json_parser
from apetizer.storages.model import ModelStore
from apetizer.views.api import ApiView
from apetizer.views.pipe import ActionPipeView


class VisitorView(ActionPipeView, ApiView):
    
    view_name = 'visitor'
    view_template = 'register/view.html'
    
    class_actions = ['validate', 'profile']
    class_actions_forms = {'profile': (VisitorForm,),
                           'validate': (VisitorValidateForm,),}
    
    class_action_templates = {'validate': 'register/validate.html',
                              'profile': 'register/profile.html',}
    
    pipe_table = ModelStore()
    
    def __init__(self, **kwargs):
        super(VisitorView, self).__init__(**kwargs)
        # TODO
        # append scenario keys to the herited one instead of replacing
        user_pipe = OrderedDict([
                                  ('email',
                                   {'class': self.__class__,
                                    'action': 'profile'}),
                                  ('username',
                                   {'class': self.__class__,
                                    'action': 'profile'}),
                                  ('validated',
                                   {'class': self.__class__,
                                    'action': 'validate'}),
                                  ])
        
        #for k,e in user_pipe.items():
        #    self.pipe_scenario[k]=e
        self.action_scenarios['profile'] = user_pipe
        self.action_scenarios['validate'] = user_pipe
    
    def get_context_dict(self, request, user_profile, input_data, **kwargs):
        template_args = super(VisitorView, self).get_context_dict(request, user_profile, input_data, **kwargs)
        return template_args

    def get_user_profile(self, request, **kwargs):
        
        akey = self.get_session_user_keys(request)
        
        try:
            visitor = Visitor.objects.filter(akey=akey, completed_date__isnull=True).order_by('-ref_time')[0]
        except IndexError:
            new_key = self.rotate_akey(request, kwargs.get('pipe'), **kwargs)
            visitor = Visitor(akey=new_key)
            visitor.locale = get_language()
            visitor.action = 'home'
            visitor.data = json.dumps(kwargs['pipe']['data'], default=API_json_parser)
            visitor.path = request.path_info
            visitor.full_clean()
            visitor.save()
        
        return visitor


    def get_final_url(self, action_data):
        """
        get a final url for the pipe action
        """
        if action_data['origin_url']:
            return action_data['origin_url']
        else:
            return self.success_url


    def get_forms_instances(self, action, user_profile, kwargs):
        if action in VisitorView.class_actions:
            return (self.get_user_profile(self.request, **kwargs),)
        else:
            return super(VisitorView, self).get_forms_instances(action, user_profile, kwargs)


    def process_profile(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Display full user profile
        """
        
        # check for an existing user account
        
        #if not user_profile.validated and template_args['currentNode'].validated:
        #    return HttpResponseRedirect(template_args['currentNode'].get_url()+'view/')
        
        return self.manage_pipe(request, user_profile, input_data, template_args, **kwargs)


    
    def process_validate(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Check for email token activation
        """
        pipe_data = kwargs['pipe']
        akey = self.get_session_user_keys(request)
        
        if input_data.get('renew', False):
            # check if email have already been sent for this session
            
            # send a new token link
            self.send_validation_link(user_profile)
        else:
            token = input_data.get('token', '')
            
            if token and user_profile.is_valid_token(token) and akey == user_profile.akey:
                
                # validate user feed
                user_feed = user_profile.get_feed()
                for event in user_feed:
                    if not event.validated \
                        or event.username != user_profile.username \
                        or event.email != user_profile.email:
                        event.username = user_profile.username
                        event.email = user_profile.email
                        event.validated = now()
                        event.save()
                
                user_profile.validated = now()
                user_profile.save()
                # validate and capture session stuff
                
            else:
                # token is not valid
                #template_args['action_forms'] = self.get_validated_forms(self.get_forms_instances(kwargs['action'], user_profile, kwargs), 
                #                                                         kwargs['pipe'], kwargs['action'], False, files=None, bound_forms=True)
            
                #return self.render(request, template_args, {}, **kwargs)
                pass
                #self.send_validation_link(user_profile)
        
        template_args['actions_to_validate'] = Visitor.objects.filter(akey=user_profile.akey, validated__isnull=True)
        
        if user_profile.validated:
            return HttpResponseRedirect(self.get_next_url(kwargs['pipe'], **kwargs))
        else:
            return self.manage_pipe(request, user_profile, input_data, template_args, **kwargs)

    def manage_pipe(self, request, user_profile, input_data, template_args, **kwargs):
        
        # create new visitor if email changes
        if user_profile and user_profile.email and 'email' in input_data and input_data['email'] \
            and input_data['email'] != user_profile.email:
            self.rotate_akey(request, kwargs.get('pipe'), **kwargs)
            return HttpResponseRedirect(self.get_reversed_action(self.view_name, 'next', kwargs))
        
        return super(VisitorView, self).manage_pipe(request, user_profile, input_data, template_args, **kwargs)
    

    def send_validation_link(self, user_profile):
        
        title = 'Email de validation'
        text = user_profile.get_url()
        html = '<a href=>'+text+'</a>'
        
        async_dispatcher = AsyncDispatcher.get_instance()
        async_dispatcher.spawn(send_validation_email, [title,text,html], {})

def send_validation_email(title, text, html):
    # call the email api
    return html

def send_email(self, origin_email, target_email, title, message, content):
    pass

