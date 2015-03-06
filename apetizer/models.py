'''
Created on Feb 11, 2015

@author: nicolas
'''
from django.db import models


class AbstractPipeModel(models.Model):
    """
    An abstract base model for forms without model
    """
    class Meta:
        abstract = True
