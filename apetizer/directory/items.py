'''
Created on 3 mars 2014

@author: rux
'''
import os

from django.conf import settings
from django.core.cache import cache as drilldown_cache
from django.template.defaultfilters import slugify
from pattern.text import fr

from apetizer.directory.drilldown import Drilldown
from apetizer.dispatchers.async import AsyncDispatcher
from apetizer.models import Item, get_new_uuid
from apetizer.storages.memcached import MemcacheStorage, DictStorage
from django.utils.translation import get_language


class ItemDrilldown(Drilldown):
    '''
    
    '''
    def load_items(self):
        
        # get parking address list of active vehicles
        if settings.DEBUG:
            print '\nStart parsing items ...'
        
        kwargs= {}
        kwargs['pipe'] = {'locale':get_language(),
                          'akey':get_new_uuid(),
                          'action':'import',
                          'status':'imported',
                          'path':'/localhost'
                          }
        
        #item = Item.objects.get_or_create_url('//localhost/', **kwargs)
        #self.add_item_data(item.id, item.get_path(), item.label, item.latitude, item.longitude, item.admin0, item.admin1, item.admin2, item.admin3)
        
        if not settings.DEBUG:
            return
        
        #return
        items = Item.objects.filter(visible=True,).order_by('parent')
        #.exclude(parent=None)
        # add each vehicle to the cache structure
        max_key_modified = 0
        
        for item in items:
            # unidex key if already exists
            if self.has_object('item', item.id):
                self.remove_object('item', item.id)
            
            keywords = []
            
            #
            if item.label:
                sentence = fr.parse(item.label)
                for word in sentence.split()[0]:
                    if word[1] == 'NN' and len(word[0]) > 2:
                        if not word[0] in keywords:
                            keywords.append(slugify(word[0]))
            
            if item.title:
                sentence = fr.parse(item.title)
                for word in sentence.split()[0]:
                    if word[1] == 'NN' and len(word[0]) > 2:
                        if not word[0] in keywords:
                            keywords.append(slugify(word[0]))
            
            if item.description:
                sentence = fr.parse(item.description)
                for word in sentence.split()[0]:
                    if word[1] == 'NN' and len(word[0]) > 2:
                        if not word[0] in keywords:
                            keywords.append(slugify(word[0]))
            
            keywords.append(item.label)
            #print keywords
            self.add_item_data(item.id, item.get_path(), item.label, keywords, item.latitude, item.longitude)
            print '.',
            #print 'added '+item.get_path()
        
        if settings.DEBUG:
            
            print '\nParsed '+str(len(items))+' items in '+str()+' seconds\n'
            return
            try:
                self.data_map.print_stats()
            except:
                pass
    
    def add_item_data(self, uid, path, label, keywords, lat, lng):
        
        if lat == None:
            lat = 0.0
        if lng == None:
            lng = 0.0
        
        obj = {
            'item': uid,
            'path':path,
            'label': label,
        }
        self.add_object( 'item', obj )
        
        for keyword in keywords:
            
            keyword_obj = {
                'keyword':keyword,
                'label':keyword,
                'path':path,
                'item':uid,
            }
            self.add_object( 'keyword', keyword_obj)
            self.add_to_bounds( 'keyword', keyword, lat, lng)


    def remove_item_data(self, uid):
        data = self.get_object('item', uid)
        self.remove_object('item', uid)


    # for invalidation population
    def update_item(self, item):
        
        self.remove_item( item.id )
        self.add_item( item )
        

SEARCH_DRILLDOWN_INDEXES = { 'keyword': {
                                  'item':('keyword', 'path', 'path-keyword', 'keyword-keyword'),
                                  'path':('keyword', 'item', 'path-keyword', 'keyword-keyword'),
                                  'keyword-keyword':('keyword', 'item', 'path-keyword', 'keyword-keyword'),
                                  'keyword':('keyword', 'item', 'path-keyword', 'keyword-keyword'),
                                  'path-keyword':('keyword', 'item', 'path', 'keyword-keyword'),
                                   },
                               }
            

def get_dict_drilldown():
    drilldown = ItemDrilldown( SEARCH_DRILLDOWN_INDEXES, 
                                                 DictStorage(), 
                                                 DictStorage())
    return drilldown


def get_memcache_drilldown():
    mem_storage = MemcacheStorage(drilldown_cache)
    drilldown = ItemDrilldown( SEARCH_DRILLDOWN_INDEXES, 
                                                 mem_storage, 
                                                 mem_storage )
    
    return drilldown


#def get_dynamodb_drilldown():
#    mem_storage = MemcacheStorage(drilldown_cache)
#    data_storage = DynamoStorage(mem_storage, settings.VEHICLE_DRILLDOWN_DYNAMO_TABLE+'-data')
#    object_storage = DynamoStorage(mem_storage, settings.VEHICLE_DRILLDOWN_DYNAMO_TABLE+'-obj')
#    drilldown = VehicleDrilldown( SEARCH_DRILLDOWN_INDEXES, 
#                                                 data_storage, 
#                                                 object_storage )
#    return drilldown


def get_default_drilldown():
    """
    :return: Drilldown object
    """
#    if settings.VEHICLE_DRILLDOWN_STORAGE == 'dynamodb':
#        drilldown = get_dynamodb_drilldown()
    if os.environ.get('DJANGO_ENV', 'dev' ) == 'production':
        drilldown = get_memcache_drilldown()
    else:
        drilldown = get_dict_drilldown()
    AsyncDispatcher.get_instance().spawn(drilldown.load_items, tuple(), {})
    return drilldown

global _search_drilldown_cache
_search_drilldown_cache = get_default_drilldown()



