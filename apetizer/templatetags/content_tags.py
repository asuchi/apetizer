'''
Created on 22 janv. 2013

@author: rux
'''
from django import template
from django.template import Template

from apetizer import models
from apetizer.utils.upload import check_permission


register = template.Library()

@register.simple_tag(takes_context=True)
def content_render( context, string ):
    return string
    t = Template( string )
    return t.render( context )

@register.inclusion_tag('content/tags/image.html', takes_context=True)
def content_item_image( context, item, width, height, display='fixed' ):
    context['image_item'] = item
    context['image_item_width'] = width
    context['image_item_height'] = height
    context['image_item_size'] = str(width)+'x'+str(height)
    context['image_item_display'] = display
    return context


@register.inclusion_tag('content/tags/breadcrumb.html', takes_context=True)
def content_breadcrumb( context, item, action=None ):
    
    context['breadcrumbAction'] = action
    if item:
        ancestors = item.get_ancestors()
        context['breadcrumbNode'] = item
        context['breadcrumbAncestors'] = ancestors
        
    return context


@register.inclusion_tag('content/tags/item.html', takes_context=True)
def content_item( context, path ):
    
    if type(path) == models.Item:
        item = path
        path = item.get_url()
    else:
        item = models.Item.objects.get_at_url( path, exact=True )

    context['item'] = item
    return context


@register.inclusion_tag('content/tags/link.html', takes_context=True)
def content_link( context, uid ):
	
	items = models.Item.objects.filter(id=id)
	if len(items):context['itemlink'] = items[0]
	
	return context


