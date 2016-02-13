'''
Created on 19 oct. 2015

@author: biodigitals
'''
import inspect
import os
import uuid

from django.core.management.base import BaseCommand, CommandError
from django.utils.html import escape

from apetizer.models import Item, Moderation, get_distincts
from apetizer.views.front import FrontView


can_import_settings = True

class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    #def add_arguments(self, parser):
    #    parser.add_argument('poll_id', nargs='+', type=int)

    def handle(self, *args, **options):
        
        # create a default root
        kwargs = {}
        akey = str(uuid.uuid4())
        kwargs['pipe'] = {'akey':akey,
                          'action':'doc',
                          'path':'/',
                          'locale':'fr',
                          'status':'added',
                          }
        
        doc_root = '/localhost'
        
        # create root for documentation if it doaes not exists yet
        #documentation = Item.objects.get_or_create_url(doc_root, **kwargs)
        #documentation.delete()
        def get_class_that_defined_method(meth):
            for cls in inspect.getmro(meth.im_class):
                if meth.__name__ in cls.__dict__: 
                    return cls
            return None
        
        doc_root = '/localhost'
        documentation = Item.objects.get_or_create_url(doc_root, **kwargs)
        documentation.visible = False
        documentation.save()
        
        doc_root = '/network'
        documentation = Item.objects.get_or_create_url(doc_root, **kwargs)
        documentation.visible = False
        documentation.save()

