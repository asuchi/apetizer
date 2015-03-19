'''
Created on 2 fevr. 2015

@author: nicolas
'''
from apetizer.forms.httpapi import HttpApiForm
from apetizer.models import AbstractPipeModel


class ActionPipeForm(HttpApiForm):
    slug = 'slug'
    title = ''
    hidden_fields = tuple()

    class Meta:
        fields = []
        model = AbstractPipeModel
