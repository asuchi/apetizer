'''
Created on 24 oct. 2013

@author: rux
'''
import inspect
import json
import logging
import os.path

from django.http import HttpResponse
from django.http.response import HttpResponseRedirect

from apetizer.models import Item
from apetizer.parsers.json import API_json_parser
from apetizer.views.action import ActionView
from django.forms.models import model_to_dict


logger = logging.getLogger(__name__)


def get_class_that_defined_method(meth):
    """
    http://stackoverflow.com/questions/3589311/get-defining-class-of-unbound-method-object-in-python-3
    """
    if inspect.ismethod(meth):
        try:
            for cls in inspect.getmro(meth.im_class):
                if meth.__name__ in cls.__dict__: 
                    return cls
        except:
            for cls in inspect.getmro(meth.__self__.__class__):
                if meth.__name__ in cls.__dict__: 
                    return cls
    elif inspect.isfunction(meth):
        return getattr(inspect.getmodule(meth),
               meth.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[0])
        
    return None

class ApiView(ActionView):
    
    class_actions = ['api', 'doc']
    class_actions_forms = {'api': [],
                           'doc': []}
    class_action_templates = {'doc':'apetizer/doc.html',
                              'api':'apetizer/api.html'}
    
    json_parser = API_json_parser

    def __init__(self, **kwargs):
        """
        Constructor. Called in the URLconf; can contain helpful extra
        keyword arguments, and other things.
        """
        # initialise the default view behavior here
        # register view_name over a global variable
        super(ApiView, self).__init__(**kwargs)
        self.__class__.get_actions()


    def render_as_json(self, request):
        """
        Tests wether the view should return json or html rendering
        """
        return os.path.splitext(request.path)[1].lower() == '.json'
    
    
    def render(self, request, template_args, result_payload=None,
               result_message="OK", result_status=200, **kwargs):
        """
        Render either json or html depending on the request
        """
        #template_args['api'] = Item.objects.get_at_url('/apetizer')
        
        if result_payload == None:
            #result_payload = self.get_input_data(request)
            result_payload = {}
            result_payload['nodes'] = []
            for node in template_args['nodes']:
                #node_item_data = model_to_dict(node)
                node_data = {}
                node_data['id'] = node.id
                node_data['start'] = node.start
                node_data['title'] = node.title
                node_data['id'] = node.id
                
                result_payload['nodes'].append(node_data)
        
        if self.render_as_json(request):
            response = self.render_json(request, result_payload,
                                        result_message,
                                        result_status, **kwargs)
        else:
            response = self.render_html(request, template_args,
                                        result_message,
                                        result_status, **kwargs)
            
        return response
    
    def render_json(self, request, payload, message='ok', status=200,
                    **kwargs):
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
    
    
    def process_api(self, request, user_profile, input_data, template_args,
                    **kwargs):
        
        if not request.user.is_staff:
            return HttpResponseRedirect(Item.objects.get_at_url('/localhost/', exact=True))
        
        api_action = input_data.get('action', ApiView.default_action)
        
        kwargs['action'] = api_action
        
        instances = self.get_forms_instances(api_action, user_profile, kwargs)
        
        template_args['action_forms'] = self.get_validated_forms(instances, 
                                                                 input_data, 
                                                                 api_action,
                                                                 bound_forms=len(instances))
        
        template_args['actions'] = self.actions
        
        template_args['api_action'] = api_action
        
        kwargs['action'] = 'api'
        
        return self.render(request, template_args, input_data, **kwargs)
    
    
    def process_doc(self, request, user_profile, input_data, template_args,
                    **kwargs):
        """
        Utility view witch provides a rendering of the view documentation. 
        The one you are watching.
        """
        clean_path = os.path.splitext(request.path_info)[0]

        if clean_path[-1] == '/':
            clean_path = clean_path[:-1]
        
        def get_documentation(request, **kwargs):
            """
            Return API documentation from action
            methods docstring and corresponding forms.
            """
            doc_string = '<p class="" ><h2 class="ui header" >' + self.__class__.__name__ + '</h2>'
            doc_string += self.__class__.__version__ + '</p>'
            if self.__class__.__doc__:
                doc_string += '<p class="ui sub header">' + self.__class__.__doc__.replace('\n', '<br />') + '</p>'

            #doc_string += '<h3 class="documentation-section-title">Actions</h3>'
            doc_actions = self.actions
            doc_actions.sort()
            for action in doc_actions:
                doc_string += '<div class="ui segment">'
                doc_string += '<div class="ui header" >'                
                doc_string += action
                doc_string += '<div class="sub header" >'
                doc_string += get_class_that_defined_method(getattr(self, 'process_' + action)).__name__
                doc_string += '</div>'
                doc_string += '</div>'
                
                doc_string += '</p>'
                if hasattr(self, 'process_' + action):
                    docstring = getattr(self, 'process_' + action).__doc__
                    if docstring:
                        doc_string += getattr(self, 'process_' + action).__doc__.replace('\n', '<br />')
                else:
                    doc_string += 'Not implemented<br/>'
                doc_string += '</p>'

                if action in self.actions_forms and len(self.actions_forms[action]):

                    #doc_string += '<h3 class="documentation-section-title">Forms</h3>'

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

        return self.render(request, template_args, input_data, **kwargs)

    
