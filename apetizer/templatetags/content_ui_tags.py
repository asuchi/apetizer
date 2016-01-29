'''
Created on Feb 27, 2015

@author: nicolas
'''
from django import template

from apetizer.models import Item, Translation
from apetizer.utils.upload import check_permission


register = template.Library()

@register.inclusion_tag('ui/tags/toolbar.html', takes_context=True)
def content_item_toolbar(context, node):
    
    # first check for user permissions on the tag
    
    # 
    
    return context




@register.inclusion_tag('ui/tags/link_add.html', takes_context=True)
def content_add_link(context, instance, label=None):
    
    target_url = instance.get_url()
    
    template_context = {
        'add_link': target_url+'add/',
        'next_link': context['request'].META['PATH_INFO'],
        'label': label,
    }
    
    app_label = instance._meta.app_label
    model_name = instance._meta.model_name
    
    # Check for permission
    if check_permission(request=context['request'], mode_name='add',
                                                    app_label=app_label,
                                                    model_name=model_name):
        template_context['has_permission'] = True
    else:
        template_context['has_permission'] = False
    template_context['has_permission'] = True
    context.update(template_context)
    
    return context
 
@register.inclusion_tag('ui/tags/link_edit.html', takes_context=True)
def content_change_link(context, instance, label=None):
    
    if isinstance(instance, Item):
        target_url = instance.get_url()+'change/'
    elif isinstance(instance, Translation):
        target_url = instance.related.get_url()+'translate/'
    else:
        target_url = instance.get_url()
    
    template_context = {
        'edit_link': target_url,
        'next_link': context['request'].META['PATH_INFO'],
        'label': label,
    }
    
    app_label = instance._meta.app_label
    #model_name = instance._meta.module_name
    
    # Check for permission
    if check_permission(request=context['request'], mode_name='change',
                                                    app_label=app_label,
                                                    model_name=None):
        template_context['has_permission'] = True
    else:
        template_context['has_permission'] = False
    
    context.update(template_context)
    
    return context


@register.inclusion_tag('ui/tags/link_delete.html', takes_context=True)
def content_delete_link(context, instance, label=None):
 
    target_url = instance.get_url()
    
    template_context = {
        'delete_link': target_url+'delete',
        'next_link': context['request'].META['PATH_INFO'],
        'label': label,
    }
    
    app_label = instance._meta.app_label
    #model_name = instance._meta.module_name
    # Check for permission
    if check_permission(request=context['request'], mode_name='delete',
                                                    app_label=app_label,
                                                    model_name=None):
        template_context['has_permission'] = True
    else:
        template_context['has_permission'] = False
    context.update(template_context)
    return context