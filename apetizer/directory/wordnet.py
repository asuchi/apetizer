'''
Created on 3 mars 2014

@author: rux

Works with python 2.7, wordnet3.0 and pattern-2.6 for word extraction
'''
import logging
import os

from django.conf import settings
from django.core.cache import cache as drilldown_cache
from django.template.defaultfilters import slugify
from django.utils.translation import get_language
from pattern.text import fr

from apetizer.directory.drilldown import Drilldown
from apetizer.dispatchers.async import AsyncDispatcher
from apetizer.models import Item, get_new_uuid
from apetizer.storages.memcached import MemcacheStorage, DictStorage


logger = logging.getLogger(__name__)


class WordnetDrilldown(Drilldown):
    '''
    
    '''
    def load_items(self):
        
        # get parking address list of active vehicles
        logger.debug('\nStart parsing items ...')
        
        kwargs= {}
        kwargs['pipe'] = {'locale':get_language(),
                          'akey':get_new_uuid(),
                          'action':'import',
                          'status':'imported',
                          'path':'/localhost'
                          }
        
        # TODO
        # manage better indexing for production
        if not settings.DEBUG:
            return
        
        items = Item.objects.filter(visible=True,).order_by('parent')
        
        for item in items:
            # unindex key if already exists
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
            self.add_item_data(item.id, item.get_path(), item.label, keywords, item.latitude, item.longitude)
            
        if settings.DEBUG:
            logger.debug('\nParsed '+str(len(items))+' items in '+str()+' seconds\n')
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
    drilldown = WordnetDrilldown( SEARCH_DRILLDOWN_INDEXES, 
                                                 DictStorage(), 
                                                 DictStorage())
    return drilldown


def get_memcache_drilldown():
    mem_storage = MemcacheStorage(drilldown_cache)
    drilldown = WordnetDrilldown( SEARCH_DRILLDOWN_INDEXES, 
                                                 mem_storage, 
                                                 mem_storage )
    
    return drilldown


def get_default_drilldown():
    """
    :return: Drilldown object
    """
    if os.environ.get('DJANGO_ENV', 'dev' ) == 'production':
        drilldown = get_memcache_drilldown()
    else:
        drilldown = get_dict_drilldown()
    AsyncDispatcher.get_instance().spawn(drilldown.load_items, tuple(), {})
    return drilldown

global _search_drilldown_cache
_search_drilldown_cache = get_default_drilldown()


