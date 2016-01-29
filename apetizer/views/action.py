'''
Created on 24 oct. 2013

@author: rux
'''
import inspect
import json
import logging
import re

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse, resolve
from django.forms.models import model_to_dict, ModelForm
from django.http import Http404
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.utils.translation import ugettext
from django.views.generic.base import View

from apetizer.forms.base import ActionModelForm, ActionPipeForm
from apetizer.parsers.json import API_json_parser, load_json


logger = logging.getLogger(__name__)


class ActionView(View):
    """
    The default base view for all views
    implementing a parser
    and a documentation
    """
    # restrict methods to post and get only
    apetizer_method_names = ['get', 'post']

    __version__ = "0.3"

    view_name = 'undefined'
    view_title = 'Undefined'
    view_template = 'base.html'

    parent_view = None
    child_views = tuple()

    default_action = 'view'
 
    class_actions = ['view']
    class_actions_forms = {'view': []}
    class_action_templates = {}

    json_parser = API_json_parser

    def __init__(self, *args, **kwargs):
        """
        Constructor. Called in the URLconf; can contain helpful extra
        keyword arguments, and other things.
        """
        # initialise the default view behavior here
        # register view_name over a global variable
        super(ActionView, self).__init__(*args, **kwargs)
        self.__class__.get_actions()

    @classmethod
    def get_actions(cls):
        class_stack = inspect.getmro(cls)[::-1]
        
        actions = []
        actions_forms = {}
        action_templates = {}
        
        for base_class in class_stack:
            
            check_classes = inspect.getmro(base_class)
            
            if ActionView in check_classes:
                #
                if not 'actions' in cls.__dict__:
                    if 'class_actions' in base_class.__dict__:
                        for action in base_class.class_actions:
                            if action not in actions:
                                actions.append(action)
                #
                if not 'actions_forms' in cls.__dict__:
                    if 'class_actions_forms' in base_class.__dict__:
                        for action in base_class.class_actions_forms:
                            actions_forms[action] = base_class.class_actions_forms[action]
                #
                if not 'action_templates' in cls.__dict__:
                    if 'class_action_templates' in base_class.__dict__:
                        for action in base_class.class_action_templates:
                            action_templates[action] = base_class.class_action_templates[action]
        
        if not 'actions' in cls.__dict__:
            cls.actions = actions
        if not 'actions_forms' in cls.__dict__:
            cls.actions_forms = actions_forms
        if not 'action_templates' in cls.__dict__:
            cls.action_templates = action_templates
        
        
        return cls.actions
    
    def manage_request(self, request):
        request.path_info = '/'+request.META['HTTP_HOST'].split(':')[0]+request.path

    def get(self, request, *args, **kwargs):
        """
        Manage a GET request
        """
        self.manage_request(request)
        if kwargs['action'] == None:
            kwargs['action'] = self.default_action
        reverse_keys = []
        for key in kwargs:
            reverse_keys.append(key)
        kwargs['reverse_keys'] = reverse_keys
        kwargs['args'] = args
        kwargs['view_name'] = resolve(request.path_info).url_name
        # parse input data
        input_data = self.get_input_data(request, **kwargs)
        # start preprocessing the request
        return self.pre_process(request, input_data, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Manage a POST request
        """
        self.manage_request(request)
        if kwargs['action'] == None:
            kwargs['action'] = self.default_action
        reverse_keys = []
        for key in kwargs:
            reverse_keys.append(key)
        kwargs['reverse_keys'] = reverse_keys
        kwargs['args'] = args
        kwargs['view_name'] = resolve(request.path_info).url_name
        # parse input data
        input_data = self.get_input_data(request, **kwargs)
        # start preprocessing the request
        return self.pre_process(request, input_data, **kwargs)

    def get_referer_path(self, request):
        """
        Get a clean referer path to the request object
        """
        
        # if the user typed the url directly in the browser's address bar
        referer = request.META.get('HTTP_REFERER')
        if not referer:
            return '/'+request.path

        # remove the protocol and split the url at the slashes
        referer = re.sub('^https?:\/\/', '', referer).split('/')
        if referer[0] != request.META.get('SERVER_NAME'):
            return '/'+request.path

        # add the slash at the relative path's view and finished
        referer = u'/' + u'/'.join(referer[1:])
        return referer

    def get_user_profile(self, request, **kwargs):
        """
        Retreive user profile from the request user
        """
        return {}

    def get_context_dict(self, request, user_profile, input_data, **kwargs):
        template_args = {}
        template_args['request'] = request
        template_args["user_profile"] = user_profile
        template_args['input_data'] = input_data
        template_args['action'] = kwargs.get('action')
        return template_args

    def get_input_data(self, request, **kwargs):
        """
        Get a dict of all the inputs merged ( GET < POST|json )

        The GET query keys are appended and updated
        by either the POST or the json['payload'] query keys

        You can change this behavior by overwritting this method in your view
        """
        data = {}

        # use the get variables first or last ?
        data.update(request.GET.dict())

        # use either the post or json data ?
        if 'application/json' in request.META.get('CONTENT_TYPE', ''):
            data.update(load_json(request.body))
        else:
            data.update(request.POST.dict())
        
        
        
        # remove csrftoken
        if 'csrfmiddlewaretoken' in data:
            del data['csrfmiddlewaretoken']

        return data
    
    def get_forms_instances(self, action, user_profile, kwargs):
        """
        Override this method to retreive instance for action
        """
        return tuple()
    
    def get_forms_data(self, *forms):
        """
        Get a data dictionnary of the provided forms instances fields data
        """
        data = {}
        for form in forms:
            data.update(form.get_data())

        return data

    def get_action_forms(self, action):
        """
        Returns a tuple with the list of forms invovlved
        """
        forms = tuple()

        if action in self.actions_forms:
            aforms = self.actions_forms[action]
        else:
            aforms = []

        for form_class in aforms:
            forms += (form_class,)

        return forms
    
    def get_validated_forms(self, form_models, 
                            input_data, action,
                            save_forms=False, files=None, bound_forms=True):
        """
        From a tuple of model instances,
        get the corresponding action forms
        You can save them manually by passing False to save_forms
        """
        if files is None:
            files = {}
        forms = tuple()
        if action in self.actions_forms:
            aforms = self.actions_forms[action]
        else:
            aforms = []
        
        instances = []
        if form_models:
            for form_class in aforms:
                for model_instance in form_models:
                    if issubclass(form_class, ActionModelForm) and \
                        isinstance(model_instance, form_class.Meta.model):
                        
                        form_data = model_to_dict(model_instance)
                        form_data.update(input_data)
                        if bound_forms:
                            form_instance = form_class(form_data,
                                                       instance=model_instance,
                                                       files=files)
                        else:
                            form_instance = form_class(initial=form_data, instance=model_instance)
                        
                        if bound_forms and save_forms and form_instance.is_valid():
                                form_instance.full_clean()
                                form_instance.save()
                                instances.append(form_instance.instance)
                        
                        forms += (form_instance,)
        
        for form_class in aforms:
            if issubclass(form_class, ActionPipeForm):
                if bound_forms:
                    form_instance = form_class(input_data)
                else:
                    form_instance = form_class(initial=input_data)
                if bound_forms and save_forms and form_instance.is_valid():
                    if issubclass(form_class, ModelForm):
                        form_instance.save()
                forms += (form_instance,)
        
        if save_forms:
            for instance in instances:
                instance.full_clean()
                instance.save()
        
        return forms

    
    def validate_action_forms(self, request, forms):
        '''
        Validates a given list of forms
        and adds validation error message to request
        '''
        if not len(forms):
            return False
        
        all_forms_valid = True
        for f in forms:
            
            if f.is_bound == False:
                all_forms_valid = False
            
            f.full_clean()
            if not f.is_valid():
                all_forms_valid = False
            
            if len(f.errors) or len(f.non_field_errors()):
                # check error field are not in hidden/ignored fields
                # and gether their errors as request messages
                for field in f.errors:
                    all_forms_valid = False
                    error_message = u'<b>%s</b> %s' % (f[field].label, f.errors[field])
                    messages.error(request, error_message)

                for message in f.non_field_errors():
                    messages.error(request, message)
                    all_forms_valid = False
            else:
                for field in f.fields:
                    try:
                        f.fields[field].run_validators(f[field].value())
                    except ValidationError as e:
                        error_message = u'<b>%s</b> %s' % (f[field].label, e.messages )
                        messages.error(request, error_message)
                        all_forms_valid = False
                        f.errors[field] = e.messages[0]

        
        return all_forms_valid



    def pre_process(self, request, input_data, **kwargs):
        """
        Hook before processing the request
        Best place to make user/objects rights management
        """
        action = kwargs.get('action', ActionView.default_action)
        
        if not self.__getattribute__('process_'+action):
            # this should not happen
            # log the event
            logger.error('Unknown process action code called')
            raise Http404
        
        # get user profile object
        user_profile = self.get_user_profile(request, **kwargs)
        
        action = kwargs.get('action', None)
        if action is None or not action:
            action = ActionView.default_action
            kwargs['action'] = action
        
        elif not action in self.actions:
            logger.debug('Missing action '+action)
            raise Http404
        
        template_args = self.get_context_dict(request, user_profile, input_data, **kwargs)
        
        return self.process(request, user_profile, input_data, template_args, **kwargs)

    def process(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Processes the request
        At this point, the template args context is initialized
        and the processing of the selected action is triggered
        It returns a response object 
        that should come from the view render method
        but any response returned by the action is accepted
        """
        
        action = kwargs.get('action', None)
        
        if self.__getattribute__('process_'+action):
            response = self.__getattribute__('process_'+action)(request,
                                                            user_profile, 
                                                            input_data,
                                                            template_args,
                                                            **kwargs)
            return response
        else:
            result_payload = input_data
            result_message = ugettext(u'Action Not implemented:'+action)
            result_status = 'error'
            return self.render(request, result_payload, result_message,
                               result_status, **kwargs)

    def process_view(self, request, user_profile, input_data, template_args,
                     **kwargs):
        """
        Returns the view action processed data
        """
        result_payload = input_data
        result_message = 'OK'
        result_status = 'success'
        return self.render(request, template_args, result_payload,
                           result_message, result_status, **kwargs)

    def render(self, request, template_args, result_payload={},
               result_message="OK", result_status=200, **kwargs):
        """
        Render either json or html depending on the request
        """
        response = self.render_html(request, template_args,
                                    result_message,
                                    result_status, **kwargs)
        return response

    def render_html(self, request, template_args,
                    result_message, result_status,
                    **kwargs):
        """
        Final Html rendering witch renders the action view template
        """
        action = kwargs.get('action', ActionView.default_action)

        if type(result_status) != type(200):
            if result_status in ('warning', 'success', 'ok'):
                result_status = 200
            else:
                result_status = 500
        
        template_args['kwargs'] = kwargs
        
        return render_to_response(self.get_template_path(action),
                                  template_args,
                                  context_instance=RequestContext(request))
    
    def get_template_path(self, action):
        return self.action_templates.get(action, self.view_template)
    
    
    def get_reversed_action(self, view_name, action, kwargs):
        """
        from a view class and action,
        reverses the action url concidering url parameters in kwargs
        kwargs['reverse_keys'] = ['key',]
        kwargs[key] = value
        """
        reverse_kwargs = {}
        for key in kwargs.get('reverse_keys'):
            reverse_kwargs[key] = kwargs[key]
        
        # override action
        reverse_kwargs['action'] = action
        
        address = reverse(kwargs['view_name'], args=kwargs['args'], kwargs=reverse_kwargs)
        return address

    def finish(self, request, response, **kwargs):
        """
        This final step provides the ability to lastly manage the response
        It's mainly usefull to attach tracking cookies
        """
        return response

