'''
Created on 16 oct. 2015

@author: biodigitals
'''
from apetizer.forms.base import ActionPipeForm
from django.forms.fields import CharField


class WorkerForm(ActionPipeForm):

    pass


class FacebookGroupForm(WorkerForm):
    
    token = CharField(max_length=1024, required=True)