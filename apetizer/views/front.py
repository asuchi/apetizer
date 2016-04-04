'''
Created on 24 juin 2015

@author: rux
'''

from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.utils.text import slugify

from apetizer.directory.items import _search_drilldown_cache
from apetizer.views.content import ContentView
from apetizer.views.directory import DirectoryView
from apetizer.views.semantic import SemanticView
from apetizer.views.ui import UIView
from apetizer.views.user import UserView


class FrontView(DirectoryView, UIView, SemanticView, UserView):
    """
    Display the service front page
    """
    view_name = "front"
    view_template = 'index.html'
    
    default_action = 'default'
    
    class_actions = ['default', 'index', 'home']
    class_action_templates = {'index':'index.html',
                              'home':'home.html'}
    
    
    def process_default(self, request, user_profile, input_data, template_args, **kwargs):
        
        if kwargs['node'].behavior \
            and kwargs['node'].behavior != kwargs['action'] \
            and kwargs['node'].behavior in self.actions:
            
            kwargs['action'] = kwargs['node'].behavior
            template_args['action'] = kwargs['action']
        else:
            kwargs['action'] = 'view'
            template_args['action'] = 'view'
        
        return self.process(request, user_profile, {}, template_args, **kwargs)
    
    
    def process_home(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Display a home page
        """
        if template_args['currentNode'].parent == None:
            template_args['projects'] = template_args['user_profile'].get_roots().filter(published=True, visible=True)
        else:
            template_args['projects'] = template_args['currentNode'].parent.get_children().filter(visible=True).exclude(id=template_args['currentNode'].id)
        
        return self.render(request, template_args, **kwargs)

    def process_index(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Display an index page
        """
        return self.render(request, template_args, **kwargs)

    def render_html(self, request, template_args, result_message, result_status,
                    **kwargs):
        
        path = kwargs['node'].id
        
        if _search_drilldown_cache.data_map.has_key(path):
            data = _search_drilldown_cache.data_map.get_key_data(path)
            for key in data:
                template_args[ slugify(key).replace('-','_') ] = data[key]
        
        if kwargs['action'] in FrontView.class_actions:
            return ContentView.render_html(self, request, template_args,
                                                   result_message, result_status,
                                                   **kwargs)
        else:
            return super(FrontView, self).render_html(request, template_args, result_message, result_status, **kwargs)
            



def handler404(request):
    response = render_to_response('404.html', {},
                                  context_instance=RequestContext(request))
    response.status_code = 404
    return response


def handler500(request):
    response = render_to_response('500.html', {},
                                  context_instance=RequestContext(request))
    response.status_code = 500
    return response


