'''
Created on Feb 10, 2015

@author: nicolas
'''
import os

from django import template


register = template.Library()

@register.inclusion_tag('apetizer/tags/debug.html', takes_context=True)
def apetizer_api_debug( context ):
    
    request = context['request']
    
    clean_path = os.path.splitext(request.path)[0]
    
    if clean_path[-1] == '/':
        clean_path = clean_path[:-1]
    
    context['apetizer_api_json_url'] = clean_path+'.json'
    context['apetizer_api_doc_url'] = clean_path+'/doc/'
    
    context['apetizer_api_html_url'] = clean_path+'/'
    
    return context