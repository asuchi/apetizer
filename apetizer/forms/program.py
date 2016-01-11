'''
Created on 28 dec. 2015

@author: biodigitals
'''
from django.forms.fields import IntegerField, CharField
from django.forms.widgets import Textarea

from apetizer.forms.base import ActionPipeForm


class ProgramEditForm(ActionPipeForm):
    
    input = CharField(max_length=1024, widget=Textarea)
    
    table = IntegerField()
    row = IntegerField()
    col = IntegerField()
