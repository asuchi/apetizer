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
from apetizer.views.api import get_class_that_defined_method
from apetizer.views.front import FrontView


can_import_settings = True

class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    #def add_arguments(self, parser):
    #    parser.add_argument('poll_id', nargs='+', type=int)

    def handle(self, *args, **options):
        
        kwargs = {}
        akey = str(uuid.uuid4())
        kwargs['pipe'] = {'akey':akey,
                          'action':'doc',
                          'path':'/',
                          'locale':'fr',
                          'status':'added',
                          }
        
        doc_root = '/localhost'
        
        documentation = Item.objects.get_or_create_url(doc_root, **kwargs)
        documentation.visible = False
        documentation.save()
        
        # project roadmap
        #roadmap = Item.objects.get_or_create_url(doc_root+'/roadmap/', **kwargs)
        #issues = Item.objects.get_or_create_url(doc_root+'/issues/', **kwargs)
        
        #
        #api = Item.objects.get_or_create_url(doc_root+'/api/', **kwargs)
        
        #
        actions = Item.objects.get_or_create_url(doc_root+'/actions/', **kwargs)
        
        # create the action vocabulary node
        actions = FrontView.get_actions()
        for action in actions:
            action_item = Item.objects.get_or_create_url(doc_root+'/actions/'+action+'/', **kwargs)
            # get the documentation function class name
            action_item.label = get_class_that_defined_method(getattr(FrontView, 'process_' + action)).__name__
            
            # get the documentation function docstring
            docstring = getattr(FrontView, 'process_' + action).__doc__
            if docstring:
                action_item.description = docstring
                    
            action_item.save()
        
        
        status = Item.objects.get_or_create_url(doc_root+'/status/', **kwargs)
        statuses = get_distincts(Moderation.objects.filter().exclude(status__isnull=True), 'status')
        for s in statuses:
            workers = Item.objects.get_or_create_url(doc_root+'/status/'+s.status, **kwargs)
        
        # create the workers list
        #workers = Item.objects.get_or_create_url(doc_root+'/api/workers/', **kwargs)
        
        # create the source code tree
        source = Item.objects.get_or_create_url(doc_root+'/', **kwargs)
        
        for root_package in ('apetizer',):# 'static', 'install.md', 'requirements.txt', 'manage.py' ):
        
            apetizer = Item.objects.get_or_create_url(doc_root+'/'+root_package+'/', **kwargs)
            for root, dirs, files in os.walk(root_package):
                
                for dir in dirs:
                    
                    if dir == '__pycache__':
                        continue
                    
                    fileitem = Item.objects.get_or_create_url(doc_root+'/'+os.path.join(root, dir), **kwargs)
                    
                    fileitem.label = 'Package'
                    fileitem.title = dir
                    
                    fileitem.save()
                    
                for file in files:
                    if file.endswith(".py"):
                        fileitem = Item.objects.get_or_create_url(doc_root+'/'+os.path.join(root, file), **kwargs)
                        
                        fileitem.label = 'Module'
                        fileitem.title = os.path.splitext(file)[0]
                        
                        try:
                            fileitem.description = __import__( os.path.splitext(os.path.join(root, file))[0].replace('/', '.') ).__doc__
                        except:
                            fileitem.description = 'Error loading module'
                        
                        file_path = os.path.join(root, file)
                        fileitem.file = file_path
                        
                        content = '<pre><code class="python">'
                        with open(file_path, 'r') as content_file:
                            content += escape(content_file.read())
                            #.replace('\n', '')
                        content += '</code></pre>'
                        
                        fileitem.content = content
                        fileitem.save()
                    
                    elif file.endswith(".html"):
                        fileitem = Item.objects.get_or_create_url(doc_root+'/'+os.path.join(root, file), **kwargs)
                        
                        #fileitem.behavior = 'upload'
                        fileitem.label = 'Template Html'
                        fileitem.title = os.path.splitext(file)[0]
                        
                        file_path = os.path.join(root, file)
                        fileitem.file = file_path
                        
                        content = '<pre><code class="html">'
                        #content = ''
                        with open(file_path, 'r') as content_file:
                            content += escape(content_file.read())
                            #.replace('\n', '')
                        content += '</code></pre>'
                        
                        fileitem.content = content
                        fileitem.save()
        
        # create the dependencies list
        install = Item.objects.get_or_create_url(doc_root+'/install/', **kwargs)
        
        # create the dependencies list
        dependencies = Item.objects.get_or_create_url(doc_root+'/requirements/', **kwargs)


