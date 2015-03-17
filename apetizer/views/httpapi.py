'''
Created on 24 oct. 2013

@author: rux
'''
import json
import logging
import os.path
import re
import traceback

from django.conf import settings
from django.core.urlresolvers import reverse
from django.forms.models import model_to_dict
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.utils.translation import ugettext
from django.views.generic.base import View

from apetizer.parsers.json import API_json_parser


global _apetizer_api_views_by_name
_apetizer_api_views_by_name = []

logger = logging.getLogger(__name__)


class HttpAPIView(View):
    """
    The default base view for all views implementing a json api interface and a documentation
    """
    # restrict methods to post and get only
    apetizer_method_names = ['get', 'post']
    
    __version__ = "0.3"
     
    view_name = 'undefined'
    view_title = 'Undefined'
    view_template = 'website.html'
    
    parent_view = None
    child_views = tuple()
    
    internal_actions = ['view', 'doc']
    
    default_action = 'view'
    
    actions = ['view', 'doc']
    actions_forms = {'view':[]}
    action_templates = {}
    
    action_forms_autosave = True
    
    json_parser = API_json_parser
    
    def __init__(self, **kwargs):
        """
        Constructor. Called in the URLconf; can contain helpful extra
        keyword arguments, and other things.
        """
        # initialise the default view behavior here
        
        # register view_name over a global variable
        _apetizer_api_views_by_name.append(self.view_name)
        
        super(HttpAPIView, self).__init__(**kwargs)
        
    @classmethod
    def get_url_regexp(cls, path=''):
        """
        Returns a multi-format and multi-action url regexp string for this view
        """
        cls_actions = []
        for a in cls.actions:
            cls_actions.append(a.replace('_','\_'))
        
        url_regexp = '^'
        url_regexp += path+'[/|(\.json)]+'
        url_regexp += '(?P<action>('
        url_regexp += '|'.join(cls_actions + cls.internal_actions)
        url_regexp += ')+)*[/|(\.json)]*$'
        
        return url_regexp
    
        
    def get(self, request, **kwargs):
        """
        Manage a GET request
        """
        # get user profile object
        user_profile = self.get_user_profile(request)
        # parse input data
        input_data = self.get_input_data(request)
        # start preprocessing the request
        return self.pre_process(request, user_profile, input_data, **kwargs)
        
    
    def post(self, request, **kwargs):
        """
        Manage a POST request
        """
        # get user profile object
        user_profile = self.get_user_profile(request)
        # parse input data
        input_data = self.get_input_data(request)
        # start preprocessing the request
        return self.pre_process(request, user_profile, input_data, **kwargs)
    
    
    def get_referer_path(self, request, default=None):
        """
        Get a clean referer path to the request object
        """
        # if the user typed the url directly in the browser's address bar
        referer = request.META.get('apetizer_REFERER')
        if not referer:
            return default
    
        # remove the protocol and split the url at the slashes
        referer = re.sub('^https?:\/\/', '', referer).split('/')
        if referer[0] != request.META.get('SERVER_NAME'):
            return default
    
        # add the slash at the relative path's view and finished
        referer = u'/' + u'/'.join(referer[1:])
        return referer
    
    
    def get_user_profile(self, request):
        """
        Retreive user profile from the request user
        """
        return None
    
    def get_user_dict(self, request, **kwargs):
        """
        Get the default templates args dict context for the user
        """
        template_args = self.get_context_dict(request, **kwargs)
        return template_args
        
    def get_context_dict(self, request, **kwargs):
        template_args = {}
        template_args['action'] = kwargs.get('action')
        
        return template_args
        
        
    def get_input_data(self, request):
        """
        Get a dict of all the inputs merged ( GET < POST|json )
        
        The GET query keys are appended and updated by either the POST or the json['payload'] query keys
        
        You can change this behavior by overwritting this method in your view
        """
        data = {}
        
        # use the get variables first or last ?
        data.update(request.GET.dict())
        
        # use either the post or json data ?
        if 'application/json' in request.META.get('CONTENT_TYPE', ''):
            data.update( json.loads(request.body) )
        else:
            data.update(request.POST.dict())
        
        # remove csrftoken
        if 'csrfmiddlewaretoken' in data:
            del data['csrfmiddlewaretoken']
        
        return data
        
    def get_forms_data(self, *forms):
        """
        Get a data dictionnary of the provided forms instances fields data
        """
        data = {}
        for form in forms:
            data.update( form.get_data() )
        
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
    
    def get_validated_forms(self, form_models, input_data, action, save_forms=None):
        """
        From a tuple of model instances, 
        get the corresponding action forms instances 
        **loaded, validated and saved** with the input_data dict
        You can save them manually by passing False to save_forms
        """
        if save_forms == None:
            save_forms = self.action_forms_autosave
        
        forms = tuple()
        if action in self.actions_forms:
            aforms = self.actions_forms[action]
        else:
            aforms = []
        
        for form_class in aforms:
            
            if form_models:
                
                for model_instance in form_models:
                    
                    if isinstance(model_instance, form_class.Meta.model):
                        
                        if len(input_data.keys()):
                            # prepare full updated dict with model and input data                        
                            form_data = model_to_dict(model_instance)
                            form_data.update(input_data)

                            # assign to form and save if changed and valid
                            form_instance = form_class(instance=model_instance, data=form_data)
                            if save_forms and form_instance.has_changed():
                                if form_instance.is_valid():
                                    form_instance.full_clean()
                                    form_instance.save()
                                    form_instance.is_saved = True
                        else:
                            form_instance = form_class(instance=model_instance)
                            
                        forms += (form_instance,)
            else:
                form_instance = form_class(instance=form_class.Meta.model(), initial=input_data)
                if save_forms and form_instance.has_changed() and form_instance.is_valid():
                    form_instance.save()
                forms += (form_instance,)
        
        return forms
     
    def pre_process(self, request, user_profile, input_data, **kwargs):
        """
        Hook before processing the request
        
        Best place to make user/objects rights management
        """
        
        return self.process(request, user_profile, input_data, **kwargs)
    
    
    def process(self, request, user_profile, input_data, **kwargs):
        """
        Processes the request
        
        At this point, the template args context is initialized
        and the processing of the selected action is triggered
        It returns a response object
        This should come from the view render method but
        Any response returned by the action is accepted
        """
        action = kwargs.get('action', None)
        if action == None:
            action = self.default_action
            kwargs['action'] = action
        elif not action in self.actions + self.internal_actions:
            raise Http404

        template_args = {}
        if request.user.is_authenticated():
            template_args = self.get_user_dict(request, **kwargs)
        else:
            template_args = self.get_context_dict(request, **kwargs)
        
        if self.__getattribute__('process_'+action):
            return self.__getattribute__('process_'+action)(request, user_profile, input_data, template_args, **kwargs)
        else:
            result_payload = input_data
            result_message = ugettext(u'Action Not implemented:'+action)
            result_status = 'error'
            return self.render(request, result_payload, result_message, result_status, **kwargs)
    
    
    def process_view(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Returns the view action processed data
        """
        result_payload = []
        result_message = 'OK'
        result_status = 'success'
        
        return self.render(request, template_args, result_payload, result_message, result_status, **kwargs)
    
    
    def render(self, request, template_args, result_payload={}, result_message="OK", result_status=200, **kwargs):
        """
        Render either json or html depending on the request
        """
        if self.render_as_json(request):
            response = self.render_json(request, result_payload, result_message, result_status, **kwargs)
        else:
            response = self.render_html(request, template_args, result_message, result_status, **kwargs)
        
        return response
    
    def render_as_json(self, request):
        """
        Tests wether the view should return json or html rendering
        """
        return os.path.splitext( request.path )[1].lower() == '.json'
    
        
    def render_html(self, request, template_args, result_message, result_status, **kwargs):
        """
        Final Html rendering witch renders the action view template
        """
        template_args['view_name'] = self.view_name
        
        if not 'data_view_url' in template_args:
            try:
                template_args['data_view_url'] = reverse(self.view_name, kwargs=kwargs)
                template_args['data_api_url'] = reverse(self.view_name, kwargs=kwargs)+'.json'
            except:
                if settings.DEBUG:
                    traceback.print_exc()
        
        if type(result_status) != type(200):
            if result_status in ('warning','success','ok'):
                result_status = 200
            else:
                result_status = 500
        
        return render_to_response( self.action_templates.get(kwargs.get('action', self.default_action),self.view_template), template_args,
                                  context_instance=RequestContext(request))
        
    def render_json(self, request, payload, message='ok', status=200, **kwargs):
        """
        Rendering a json response from payload, message and status
        """
        if message is None:
            message = 'OK'
        
        json_result = {'message': message,
                       'status': status,
                       'payload': payload}
        
        json_string = json.dumps(json_result, default=self.json_parser)
        
        return HttpResponse(json_string, content_type='application/json')
    
    
    def finish(self, request, response, **kwargs):
        """
        This final step provides the ability to lastly manage the response
        It's mainly usefull to attach tracking cookies
        """
        return response
    
    
    def process_doc(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Utility view witch provides a rendering of the view documentation. The one you are watching.
        """
        clean_path = os.path.splitext(request.path)[0]
        
        if clean_path[-1] == '/':
            clean_path = clean_path[:-1]
        
        template_args['apetizer_api_base_url'] = clean_path
        
        template_args['apetizer_api_json_url'] = clean_path+'.json'
        template_args['apetizer_api_doc_url'] = clean_path+'.doc'
        
        template_args['apetizer_api_html_url'] = clean_path+'/'
        
        
        def get_documentation(request, **kwargs):
            """
            Return API documentation from action methods docstring and corresponding forms.
            """
            
            doc_string = '<p><h1 class="documentation-section-title" >' + self.__class__.__name__ + '</h1> '
            doc_string += self.__class__.__version__ + '</p>'
            
            if self.__class__.__doc__:
                doc_string += '<h2>' + self.__class__.__doc__.replace('\n', '<br />') + '</h2>'
            
            doc_string += '<h3 class="documentation-section-title">Actions</h3>'
            
            for action in self.actions:
                doc_string += '<div class="documentation-action">'
                doc_string += '<p>'
                doc_string += '<b>'+action+' :</b>'
                if hasattr(self, 'process_' + action):
                    docstring = getattr(self, 'process_' + action).__doc__
                    if docstring:
                        doc_string += getattr(self, 'process_' + action).__doc__.replace('\n', '<br />')
                else:
                    doc_string += 'Not implemented<br/>'
                doc_string += '</p>'
                
                if action in self.actions_forms and len(self.actions_forms[action]):
                    
                    doc_string += '<h3 class="documentation-section-title">Forms</h3>'
    
                    for form in self.actions_forms[action]:
                        doc_string += '<div class="documentation-form" >'
                        
                        doc_string += '<h4>' + form.__name__ + '</h4>'
                        if form.__doc__:
                            doc_string += '<p><i>' + form.__doc__.replace('\n', '<br />') + '</i></p>'
    
                        doc_string += '<ul>'
                        for field_name in form.__dict__['declared_fields']:
                            doc_string += '<li><b>' + str(field_name) + '</b> '
                            if form.__dict__['declared_fields'][field_name].required:
                                doc_string += ' (required)'
                            doc_string += '<span class="pull-right" >'
                            doc_string += form.__dict__['declared_fields'][field_name].__class__.__name__
                            doc_string += '</span><br />'
                            if form.__dict__['declared_fields'][field_name].help_text:
                                doc_string += 'Help text: '
                                doc_string += form.__dict__['declared_fields'][field_name].help_text._proxy____args[0] # ignoring proxy field
                            doc_string += '</li>'
    
                        doc_string += '</ul>'
                        doc_string += '</div>'
                doc_string += '</div>'
                
            return doc_string
        
        template_args['content'] = get_documentation(request, **kwargs)
        
        return render_to_response('documentation.html', template_args,
                                  context_instance=RequestContext(request))
