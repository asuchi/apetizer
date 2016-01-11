from django import template
from django.utils.timezone import now

from apetizer.forms.moderate import ModerateCommentForm
from apetizer.models import Moderation


register = template.Library()

@register.inclusion_tag('moderate/tags/comment_panel.html', takes_context=True )
def moderate_panel(context, document):
    context['comment_form'] = ModerateCommentForm
    return context

@register.inclusion_tag('moderate/tags/moderation_stars.html', takes_context=True )
def moderate_evaluation(context, model={'editable': True}):
    context['model'] = model
    return context

@register.inclusion_tag('moderate/tags/moderation_stars.html', takes_context=True )
def moderate_average_evaluation(context, document):
    moderations = Moderation.objects.filter(related=document, status='comment', visible=True)
    evaluation = 0
    n = 0
    total = 0
    nan = False
    for moderation in moderations:
        n+=1
        total+= moderation.evaluation
    if n == 0: 
        nan = True
        evaluation = 0
    else :
        evaluation = int(float(total)/n)
    
    context['model'] = {
            'editable' :  False, 
            'evaluation' : evaluation,
            'nan' : nan
        }
    return context
