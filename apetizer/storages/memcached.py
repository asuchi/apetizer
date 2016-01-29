'''
Created on 2 mars 2014

@author: rux
'''
import json
import logging
import zlib

from apetizer.parsers.json import dump_json, load_json
from apetizer.utils.compatibility import unicode3


logger = logging.getLogger(__name__)

class DictStorage():
    '''
    Default basic memory storage for drilldown
    
    It handle the in memory drilldown
    
    the keys are serialized and stored using their unicode representation
    and key as strings are forced to unicode internaly
    
    '''
    
    prefix = ''
    
    # 
    def __init__(self):
        self.values = {}
    
    def has_key(self, key):
        return self._conform_key(key) in self.values
    
    def get_key_data(self, key):
        return self.values[self._conform_key(key)]
    
    def set_key_data(self, key, value):
        self.values[self._conform_key(key)] = value
        return True
    
    def remove_key_data(self, key):
        if key in self.values:
            del self.values[self._conform_key(key)]
            return True
        else:
            return False
    
    def _conform_key(self,key):
        return key
        if type(key) == type(''):
            key = unicode3(key)
        key = repr(key)
        return self.prefix+key
    
    def lock(self):
        self.is_locked = True
    
    def flush(self):
        self.is_locked = False
    
    def print_stats(self):
        '''
        Print debug and stats about the structure size
        '''
        log = 'Data map has now '+str(len( self.values ))+' paths \n'
        log += self.values.keys()+'\n'
        
        total_size = 0
        average_size = 0
        max_size = 0
        min_size = None
        max_size_path = None
        
        oversized_keys = []
        allowed_max_size = 4*(1024)
        
        for path in self.values.keys():
            size = len( zlib.compress(json.dumps(self.values[path])) )
            average_size = (float(average_size)+size)/2
            if size > max_size:
                max_size = size
                max_size_path = path
            if size < min_size or min_size == None:
                min_size = size
            total_size+=size
            if size > allowed_max_size:
                oversized_keys.append( (path,size) )
        
        log += 'Data map index now '+str( float(total_size)/(1024*1024) )+' Mo'+'\n'
        log += 'Average key size is '+str( float(average_size)/(1024) )+' Ko'+'\n'
        log += 'Minimum key size is '+str( float(min_size)/(1024) )+' Ko'+'\n'
        log += 'Maximum key size is '+str( float(max_size)/(1024) )+' Ko at '+str(max_size_path)+'\n'
        
        log += 'More than 4k keys:'+'\n'
        for key in oversized_keys:
            log += '\t'+str(key[0])+' - '+str( float(key[1])/(1024) )+' Ko'+'\n'
        
        logger.debug(log)
        
        return
        
        log += 'Towns with wrong geocoded vehicle:',
        wrong_town_geocode_count = 0
        for key in self.object_map['town']:
            if len(self.values[key]['country']) > 1 or len(self.values[key]['region']) > 1 or len(self.values[key]['dept']) > 1:
                wrong_town_geocode_count += 1
                
        log += wrong_town_geocode_count
        
        log += 'Vehicles with potential wrong geocoded town:',
        wrong_geocode_count = 0
        for key in self.object_map['pa']:
            town = self.object_map['pa'][key]['data']['town']
            if len(self.values[town]['country']) > 1 or len(self.values[town]['region']) > 1 or len(self.values[town]['dept']) > 1:
                wrong_geocode_count+=1
        
        log += wrong_geocode_count
        
        log += '\n'
    
DIRECTORY_CACHE_PREFIX = 'dir-'
DIRECTORY_VERSION = '1'

class MemcacheStorage():
    '''
    Memcached Drilldown Layer
    
    Basically, it serializes/deserialize the data by key
    '''
    prefix = DIRECTORY_CACHE_PREFIX+'-'+DIRECTORY_VERSION+'-'
    
    # 
    def __init__(self, cache, language='fr'):
        self.prefix = DIRECTORY_CACHE_PREFIX+'-'+DIRECTORY_VERSION+'-'+language+'-'
        self.cache = cache
    
    # 
    def has_key(self, key):
        value = self.cache.get(self._conform_key(key))
        if value != None:
            return True
        else:
            return False
    
    def get_key_data(self, key):
        value = self.cache.get(self._conform_key(key))
        if value:
            return self._deserialize(value)
        else:
            return None
    
    def set_key_data(self, key, value):
        self.cache.set(self._conform_key(key), self._serialize(value), 0 )
        return True
    
    def remove_key_data(self, key):
        self.cache.set(self._conform_key(key), None)
        return True
    
    def _serialize(self, data):
        return dump_json(data)
    
    def _deserialize(self, data):
        return load_json(data)
    
    def _conform_key(self,key):
        if type(key) != type(u''):
            key = unicode3(key)
        key = repr(key)
        return str(self.prefix+key)

    def lock(self):
        self.is_locked = True
    
    def flush(self):
        self.is_locked = False


