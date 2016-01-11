'''
Created on 2 mars 2014

@author: rux
'''
import json
import pprint
import re

from django.conf import settings
from django.http.response import Http404
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.template.defaultfilters import slugify

from apetizer.directory.items import _search_drilldown_cache
from apetizer.models import Item
from apetizer.views.action import ActionView


class DirectoryView(ActionView):
    
    class_actions = ['directory']
    class_action_templates = {'directory':'search/directory.html'}
    
    def process_directory(self, request, user_profile, input_data, template_args, **kwargs):
        
        #path = '/'.join(kwargs['path'].split('/')[1:-1])
        path = kwargs['path']
        
        if path == '/':
            path = 'root'
        
        re_uuid = re.compile("[0-F]{8}-[0-F]{4}-[0-F]{4}-[0-F]{4}-[0-F]{12}", re.I)
        if re_uuid.findall(path):
            path = kwargs['node'].id
        
        if _search_drilldown_cache.data_map.has_key(path):
            data = _search_drilldown_cache.data_map.get_key_data(path)
            print data
            for key in data:
                template_args[ slugify(key).replace('-','_') ] = data[key]
            
            if 'item' in data:
                if len(data['item']) < 250:
                    template_args['nodes'] = Item.objects.filter(id__in=data['item'].keys())
            else:
                template_args['nodes'] = []
        else:
            print 'No path '+path
            if settings.DEBUG:
                print _search_drilldown_cache.data_map.values.keys()[:100]
            raise Http404
        
        return self.render(request, template_args, data, **kwargs)
