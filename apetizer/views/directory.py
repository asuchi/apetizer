'''
Created on 2 mars 2014

@author: rux
'''
import json
import logging
import pprint
import re

from django.conf import settings
from django.http.response import Http404
from django.template.defaultfilters import slugify

from apetizer.directory.items import _search_drilldown_cache
from apetizer.forms.search import DirectoryQueryForm
from apetizer.models import Item
from apetizer.views.action import ActionView


logger = logging.getLogger(__name__)

class DirectoryView(ActionView):
    
    class_actions = ['directory', 'query']
    class_actions_forms = {'query':(DirectoryQueryForm,)}
    class_action_templates = {'directory':'search/directory.html'}
    
    def process_query(self, request, user_profile, input_data, template_args, **kwargs):
        
        query = input_data.get('query')
        if not query:
            return self.render(request, template_args, {}, 'Missing query string', 'error', **kwargs)
        
        result_keys = []
        # check for words starting with query
        for key in _search_drilldown_cache.data_map.values.keys():
            if key.startswith(query):
                result_keys.append(key)
        
        results = {}
        for key in result_keys:
            
            # get the corresponding item data
            key_data = _search_drilldown_cache.data_map.get_key_data(key)
            if not 'item' in key_data:
                continue
            
            items = Item.objects.filter(id__in=key_data['item'].keys())
            
            for item in items:
                r_id = item.id
                r_url = item.get_url()
                r_label = item.label
                r_title = item.title
                r_description = item.description[:50]
                
                if not r_label in results:
                    results[r_label] = {}
                
                if not 'results' in results[r_label]:
                    results[r_label]['results'] = []
                
                results[r_label]['name'] = r_label
                results[r_label]['results'].append({'uid':str(r_id), 'url':r_url, 'title':r_title, 'description':r_description})
        
        results_payload = {}
        if len(results):
            results_payload['success'] = True
            results_payload['results'] = results
        else:
            results_payload['success'] = True
            results_payload['results'] = []
        
        return self.render(request, template_args, results_payload, 'OK', 'success',)
        
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
            for key in data:
                template_args[ slugify(key).replace('-','_') ] = data[key]
            
            if 'item' in data:
                if len(data['item']) < 250:
                    template_args['nodes'] = Item.objects.filter(id__in=data['item'].keys())
            else:
                template_args['nodes'] = []
        else:
            logger.debug('No path '+path)
            if settings.DEBUG:
                logger.debug(_search_drilldown_cache.data_map.values.keys()[:100])
            raise Http404
        
        return self.render(request, template_args, data, **kwargs)
