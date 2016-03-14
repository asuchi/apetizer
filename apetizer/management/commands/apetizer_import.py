'''
Created on 19 oct. 2015

@author: boxintime
'''

import json
import traceback
import uuid

from apetizer.models import Item, Translation
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand




class Command(BaseCommand):
    help = 'Import apetizer exported models'

    def add_arguments(self, parser):
        parser.add_argument('doc_root', nargs='+', type=int)

    def handle(self, *args, **options):
        
        # the root slug in witch you import data (www.example.com, localhost or uid ...)
        doc_root = args[0]
        json_data = json.load(file('exports/'+doc_root+'.json', 'ra'))
        
        # rebuild dict with the corresponding items
        self.item_roots = []
        self.items_by_pk = {}
        
        for odt in json_data:
            
            if odt['model'] == 'apetizer.item':
                
                if not odt['pk'] in self.items_by_pk:
                    self.items_by_pk[odt['pk']] = {}
                    self.items_by_pk[odt['pk']]['children'] = []
                    self.items_by_pk[odt['pk']]['translations'] = []
                
                self.items_by_pk[odt['pk']]['data'] = odt
            
        for odt in json_data:
            
            if odt['model'] == 'apetizer.item':
                
                if not odt['fields']['parent']:
                    self.item_roots.append(odt['pk'])
                else:
                    self.items_by_pk[odt['fields']['parent']]['children'].append(odt['pk'])
                
            if odt['model'] == 'apetizer.translation':
                
                self.items_by_pk[odt['fields']['model']]['translations'].append(odt)
        
        #
        kwargs = {}
        akey = str(uuid.uuid4())
        kwargs['pipe'] = {'akey':akey,
                        'action':'import',
                        'path':'/'+doc_root,
                        'status':'imported',
                        'locale':'fr'
                        }
        
        # delete possible existing doc_root
        try:
            Item.objects.get_or_create_url('/'+doc_root, **kwargs).delete()
        except:
            traceback.print_exc()
        
        root_node = None
        
        for pk in self.item_roots:
            if self.items_by_pk[pk]['translations'][0]['fields']['slug'] == 'home':
                for tr in self.items_by_pk[pk]['translations']:
                    tr['fields']['slug'] = doc_root
                    print tr
                root_node = self.create_item(None, pk, kwargs)
        
        if not root_node:
            raise 'Error'
        
        for root in self.item_roots:
            # create the items
            item = self.create_item(root_node, root, kwargs)
            for children in self.items_by_pk[root]['children']:
                self.create_item(item, children, kwargs)
            
            print self.items_by_pk[root]['children']
            
        return

    def create_item(self, parent, pk, kwargs):
        
        obj_dt = self.items_by_pk[pk]
        
        kwargs['pipe']['locale'] = 'fr'
        
        # create the item
        item = Item(slug=obj_dt['translations'][0]['fields']['slug'],
                    label=obj_dt['translations'][0]['fields']['label'],
                    title=obj_dt['translations'][0]['fields']['title'],
                    description=obj_dt['translations'][0]['fields']['description'],
                    content=obj_dt['translations'][0]['fields']['content'],
                    
                    published=obj_dt['data']['fields']['published'],
                    order=obj_dt['data']['fields']['order'],
                    
                    **kwargs['pipe'])
        if parent:
            item.parent_id = parent.id
        
        item.save()
        
        # add other translations
        for translation in obj_dt['translations'][1:]:
        
            translation = Translation(related_id=item.id,
                                        slug=translation['fields']['slug'],
                                        label=translation['fields']['label'],
                                        title=translation['fields']['title'],
                                        description=translation['fields']['description'],
                                        content=translation['fields']['content'],
                                       **kwargs['pipe'])
            translation.save()
        
        return item
