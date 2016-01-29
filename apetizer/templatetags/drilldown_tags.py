'''
Created on 31 mai 2013

@author: rux
'''
from collections import OrderedDict
import traceback

from django.core.urlresolvers import reverse
from django.template.defaulttags import register
from django.utils.text import slugify
from django.utils.translation import ugettext as _

from apetizer.directory.items import _search_drilldown_cache


@register.filter
def directory_key_url( key ):
    return key+'/directory/'
    return reverse('front', kwargs={'path':key, 'action':'directory'})

@register.filter
def drilldown_key_count( slug, obj_type ):
    
    #if slug.startswith(obj_type):
    #    slug = slug[len(obj_type+'-'):]
    
    try:
        if _search_drilldown_cache.has_key(slug) \
            and obj_type in _search_drilldown_cache.get_key_data(slug).keys():
            
            return  _search_drilldown_cache.get_key_data(slug)[obj_type][slug]
        else:
            return _search_drilldown_cache.get_object(obj_type, slug)['count']
    except:
        traceback.print_exc()
        return '?'


@register.filter
def drilldown_key_label( slug, obj_type ):
    
    try:
        slugs = slug.split('/')
        
        if len(slugs) == 1:
            
            if _search_drilldown_cache.has_object(obj_type, slug):
                label = _search_drilldown_cache.get_object(obj_type, slug)['data']['label']
                return label.capitalize()
            else:
                return slug.capitalize()
        else:
            
            if obj_type in ('admin3','admin2'):
                label = _search_drilldown_cache.get_object(obj_type, slugs[0])['data']['label']
            elif obj_type in ('label','slug'):
                label = _search_drilldown_cache.get_object(obj_type, slugs[1])['data']['label']
            else:
                return slug.capitalize()
    
            return label.capitalize()
    except:
        return slug.capitalize()

@register.filter
def drilldown_key( slug, obj_type ):
    label = u''
    try:
        slugs = slug.split('/')
        
        if len(slugs) == 1:
            
            if _search_drilldown_cache.has_object(obj_type, slug):
                label = _search_drilldown_cache.get_object(obj_type, slug)['data']['label']
                label = label.capitalize()
            else:
                label = slug.capitalize()
        else:
            
            if obj_type in ('admin3','admin2'):
                label = _search_drilldown_cache.get_object(obj_type, slugs[0])['data']['label']
            elif obj_type in ('label','slug'):
                label = _search_drilldown_cache.get_object(obj_type, slugs[1])['data']['label']
            else:
                label = slug.capitalize()
    
            label = label.capitalize()
    except:
        label = slug.capitalize()
    
    if _search_drilldown_cache.has_key(slug):
        label += ' ('+_search_drilldown_cache.get_key_data(slug)[obj_type]+')'
    
    return label

@register.filter
def drilldown_item_label( slug, obj_type ):
    
    return obj_type

    return _(u'')
    
    if obj_type == 'make':
        pass
    elif obj_type == 'type':
        return _(u'Rent a ')
    
    elif obj_type == 'town':
        return _(u'Rent in ')
    
    elif obj_type == 'region':
        return _(u' Rent in ')
    
    elif obj_type == 'dept':
        return _(u' Rent in ')

    elif obj_type == 'country':
        return _(u'  Rent in ')
    
    return _(u'Car rental ')


@register.filter
def drilldown_item_title( slug, obj_type ):
    title = drilldown_key_label(slug,obj_type)
    return title

@register.filter
def drilldown_item_attrs( slug, obj_type ):
    
    attributes = u''
    
    if obj_type in ( 'admin3-label', 'admin3-slug', 'admin2-label', 'admin2-slug'):
        slug = slug.split('/')[0]
        obj_type = obj_type.split('-')[0]
    
    data = _search_drilldown_cache.get_object(obj_type, slug)
    
    attributes += 'data-slug='+slug+' '
    attributes += 'data-type='+obj_type+' '
    if 'stats' in data and 'lat' in data['stats']:
        attributes += 'data-lat='+str(data['stats']['lat'])+' '
        attributes += 'data-lng='+str(data['stats']['lng'])+' '
        attributes += 'data-radius='+str(data['stats']['radius'])+' '
        attributes += 'data-count='+str(data['stats']['count'])+' '
    
    return attributes




@register.inclusion_tag('search/pages/france_top_towns.html', takes_context=True)
def drilldown_france_top_towns(context):
    
    # for each dept, get top town
    _data = _search_drilldown_cache.get_key_data('france')
    
    top_towns = {}
    
    for dept in _data['admin2'].keys():
        
        dept_data = _search_drilldown_cache.get_key_data(dept)
        
        if dept == 'paris':
            top_towns[dept] = drilldown_key_count(dept,'admin2')
        else:
            # find top town iun departement
            top_dept_count = 0
            top_dept_town = None
            
            for town, count in dept_data['admin3'].items():
                if count > top_dept_count:
                    top_dept_count = count
                    top_dept_town = town
            
            top_towns[top_dept_town] = top_dept_count
    
    # sort top_towns
    # sort town list by count
    sorted_dict = OrderedDict()
    #town_list = sorted(top_towns.iteritems(), key=lambda (k,v): (v,k), reverse=True)[0:20]
    town_list = []
    for kv in town_list:
        sorted_dict[kv[0]] = kv[1]
    
    context['top_france_town_list'] = sorted_dict
    
    
    return context


@register.inclusion_tag('search/drilldown.html', takes_context=True)
def drilldown_item(context, item):
    
    
    # for each dept, get top town
    data = _search_drilldown_cache.get_key_data(item.label)
    
    for key in data:
        context[ slugify(key).replace('-','_') ] = data[key]
    
    
    return context






