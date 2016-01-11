'''
Created on 12 mai 2015

@author: rux
'''
from django import template

register = template.Library()

@register.inclusion_tag('content/tags/moment_from_now.html', takes_context=True)
def moment_from_now( context, dt ):
    context['python_moment_datetime'] = dt
    return context

