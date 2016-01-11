'''
Created on 22 janv. 2013

@author: rux
'''
from django import template
from django.template import Template

from apetizer import models
from apetizer.models import Item
from apetizer.utils.upload import check_permission


register = template.Library()

@register.simple_tag(takes_context=True)
def content_path_switch( context ):
    current_path = context['request'].path
    if current_path.endswith('/'):
        return current_path[:-1]
    else:
        return current_path+'/'

@register.simple_tag(takes_context=True)
def content_render( context, string ):
    return string
    t = Template( string )
    return t.render( context )

@register.simple_tag(takes_context=True)
def content_title( context, path ):
    #return self.string
    try:
        item = Item.objects.get_at_url(path)
        if item:
            return item.title
        else:
            return ''
    except:
        return ''


@register.inclusion_tag('content/tags/item_image.html', takes_context=True)
def content_item_image( context, item, width, height, display='fixed' ):
    context['image_item'] = item
    context['image_item_width'] = width
    context['image_item_height'] = height
    context['image_item_size'] = str(width)+'x'+str(height)
    context['image_item_display'] = display
    return context


@register.inclusion_tag('content/tags/item_medias.html', takes_context=True)
def content_item_medias( context, item, width, height ):
    context['image_item_width'] = width
    context['image_item_height'] = height
    return context


@register.inclusion_tag('content/tags/empty.html', takes_context=True)
def get_item_object( context, path, key='item', type=None ):
    
    try:
        item = models.Item.objects.get_at_url( path )
        
        if type == 'catalog':
            pass
        elif type == 'product':
            pass
        else:
            pass
        
        context[key] = item
    except:
        pass
    
    return context

@register.inclusion_tag('content/tags/breadcrumb.html', takes_context=True)
def content_breadcrumb( context, item, action=None ):
    
    context['breadcrumbAction'] = action
    
    if item:
       
        ancestors = item.get_ancestors()
        
        context['breadcrumbNode'] = item
        context['breadcrumbAncestors'] = ancestors
        
        if not 'user' in context or context['user'].is_anonymous() or not context['user'].is_authenticated():
            context['has_permission'] = False
        else:
            context['has_permission'] = check_permission( context['request'], 'change', 'content', 'Translation' ),
    
    return context


@register.inclusion_tag('content/tags/knowmore.html', takes_context=True)
def content_knowmore( context, slug ):
    
    path = models.Item.objects.get_clean_path( context['request'].path )+'/'+slug
    
    template_context = {}
    
    # get current Item
    item = models.Item.objects.get_at_url( path )
    
    context['path'] = path
    context['item'] = item
    
    if context['user'].is_anonymous() or not context['user'].is_authenticated():
        context['has_permission'] = False
    else:
        context['has_permission'] = check_permission( context['request'], 'change', 'content', 'item' ),
    
    return context


@register.inclusion_tag('content/tags/item.html', takes_context=True)
def content_item( context, path ):
    
    if type(path) == models.Item:
        item = path
        path = item.get_url()
    else:
        item = models.Item.objects.get_at_url( path, exact=True )

    context['item'] = item
    context['has_permission'] = check_permission( context['request'], 'change', 'content', 'item' ),
    return context

@register.inclusion_tag('content/tags/map.html', takes_context=True)
def content_map( context, path ):
    
    if path == '':
        item = None
    else:
        item = models.Item.objects.get_at_url( path )
    
    roots = models.Item.objects.filter( parent=item )
    
    #context['path'] = path
    #context['item'] = item
    
    if context['user'].is_anonymous() or not context['user'].is_authenticated():
        context['has_permission'] = False
    else:
        context['has_permission'] = check_permission( context['request'], 'change', 'content', 'item' ),
    
    context['map'] = roots
    #context['nodes'] = roots
    
    return context

@register.inclusion_tag('content/tags/tile.html', takes_context=True)
def content_tile( context, path ):
    
    if path == '':
        item = None
    else:
        item = models.Item.objects.get_at_url( path )
    
    roots = models.Item.objects.filter( parent=item )
    
    #context['path'] = path
    #context['item'] = item
    
    if context['user'].is_anonymous() or not context['user'].is_authenticated():
        context['has_permission'] = False
    else:
        context['has_permission'] = check_permission( context['request'], 'change', 'content', 'item' ),
    
    context['map'] = roots
    #context['nodes'] = roots
    
    return context



@register.inclusion_tag('content/tags/sitemap.html', takes_context=True)
def content_sitemap( context, path=None ):
    if context.get('objects') == None:
        context['nodes'] = Item.objects.all()
    else:
        context['nodes'] = context.get('objects')
    return context

@register.inclusion_tag('content/tags/search.html', takes_context=True)
def content_search( context ):
    return context


@register.inclusion_tag('content/tags/menu.html', takes_context=True)
def content_menu( context, path ):
    
    if path == '' or path == '/':
        item = models.Item.objects.get_at_url( path )
        roots = models.Item.objects.filter(parent=None)
    else:
        try:
            item = models.Item.objects.get_at_url( path )
            if not item.is_leaf_node():
                roots = item.get_children()
            else:
                if item.parent != None:
                    roots = item.parent.get_children()
                else:
                    roots = models.Item.objects.filter(parent=None)
        except:
            item = None
            roots = models.Item.objects.filter(parent=None)

        
    context['path'] = path
    context['item'] = item
    
    if context['user'].is_anonymous() or not context['user'].is_authenticated():
        context['has_permission'] = False
    else:
        context['has_permission'] = check_permission( context['request'], 'change', 'content', 'item' ),
    
    context['menu'] = roots
    #context['nodes'] = roots
    
    return context

@register.inclusion_tag('content/tags/related.html', takes_context=True)
def content_related( context, path, recurse=False ):
    
    
    roots = []
    try:
        item = models.Item.objects.get_at_url( path )
            
        roots = item.related.all()
    except:
        item = None
    
    #item = models.Item.objects.get_at_url( path )
    #roots = item.related
    
    
    context['path'] = path
    context['node'] = item
    
    if context['user'].is_anonymous() or not context['user'].is_authenticated():
        context['has_permission'] = False
    else:
        context['has_permission'] = check_permission( context['request'], 'change', 'content', 'item' ),
    
    context['related'] = roots
    return context
   

@register.inclusion_tag('content/tags/tags.html', takes_context=True)
def content_tags( context, path, recurse=False ):
    
    item = models.Item.objects.get_at_url( path )
    
    roots = []
    
    for tag in item.tags.all():
        roots.append( tag.item )
    
    context['path'] = path
    context['node'] = item
    
    if context['user'].is_anonymous() or not context['user'].is_authenticated():
        context['has_permission'] = False
    else:
        context['has_permission'] = check_permission( context['request'], 'change', 'content', 'item' ),
    
    context['tags'] = roots
    #context['nodes'] = roots
    
    return context

@register.inclusion_tag('content/tags/widget.html', takes_context=True)
def content_widget( context, slug ):
    
    path = models.Item.objects.get_clean_path( context['request'].path )+'/'+slug
    
    template_context = {}
    
    # get current Item
    item = models.Item.objects.get_at_url( path )
    
    context['path'] = path
    context['item'] = item
    
    if context['user'].is_anonymous() or not context['user'].is_authenticated():
        context['has_permission'] = False
    else:
        context['has_permission'] = check_permission( context['request'], 'change', 'content', 'item' ),
    
    return context
   
   
@register.inclusion_tag('content/tags/link.html', takes_context=True)
def content_link( context, uid ):
	
	items = models.Item.objects.filter( uid=uid )
	if len(items):context['itemlink'] = items[0]
	
	return context


