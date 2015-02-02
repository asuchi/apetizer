'''
Created on 2 févr. 2015

@author: nicolas
'''
from django.db import models
from parsley.decorators import parsleyfy

from apetizer.forms.httpapi import HttpApiForm


class AbstractPipeModel(models.Model):
    class Meta:
        abstract = True

@parsleyfy
class ActionPipeForm(HttpApiForm):
    slug = 'slug'
    title = ''
    hidden_fields=tuple()
    
    class Meta:
        model = AbstractPipeModel