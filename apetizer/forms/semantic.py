'''
Created on 12 janv. 2016

@author: biodigitals
'''
from django.forms.fields import CharField
from django.forms.widgets import Textarea

from apetizer.forms.base import ActionPipeForm


class SemanticDescribeForm(ActionPipeForm):
    """
    Input necessary to process a new attribute desciption
    """
    attribut_name = CharField(max_length=200)
    attribut_type = CharField(max_length=200)
    attribut_comment = CharField(max_length=1024, widget=Textarea)

    
class SemanticEditForm(ActionPipeForm):
    """
    Input necessary to process a data attribute
    """
    property_name = CharField(max_length=200)
    property_value = CharField(max_length=200)
    