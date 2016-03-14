'''
Created on 10 oct. 2013

@author: rux
'''
import json
import logging
from time import time
import traceback

from django.conf import settings

from apetizer.parsers.api_json import load_json
import boto.dynamodb2
from boto.dynamodb2.fields import HashKey, RangeKey
from boto.dynamodb2.table import Table


logger = logging.getLogger(__name__)

#http://blog.celingest.com/en/2013/10/02/dynamodb-local-development/

class DynamoTable(object):
    
    conn = None
    table = None
    
    table_name = 'test-table'
    hash_key = 'hash_key'
    range_key = 'range_key'
    indexes = []
    
    read_units = 10
    write_units = 10
    
    counters = {'reads':0,'writes':0,'delete':0,'batch_w':0}
    
    def __init__(self, table_name, hash_key, range_key, indexes, read_units=10, write_units=10 ):
        
        self.table_name = table_name
        self.hash_key = hash_key
        self.range_key = range_key
        self.indexes = indexes
        
        self.read_units = read_units
        self.write_units = write_units
        
        try:
            self.connect()
            self.setup()
        except:
            logger.warn('Unable to connect or handle DynamoDB Table')
            traceback.print_exc()
        
    def connect(self):
        
        # create initial database tables
        self.conn = boto.dynamodb2.connect_to_region( settings.AWS_DYNAMODB_REGION,
                                                     aws_access_key_id=settings.AWS_DYNAMODB_ACCESS_KEY_ID,
                                                     aws_secret_access_key=settings.AWS_DYNAMODB_SECRET_ACCESS_KEY
                                                     )
    
    def setup(self):
        '''
        Set's up the table schema if table does not exists yet
        Return the Table
        '''
        try:
            self.table = Table.create(self.table_name, connection=self.conn, schema=[
                                                               HashKey(self.hash_key),
                                                               RangeKey(self.range_key),
                                                               ],
                                                               throughput={'read':self.read_units,'write':self.write_units})
            logger.warning('Created new DynamoDB Table')
        except:
            self.table = Table(self.table_name, connection=self.conn, schema=[
                                                               HashKey(self.hash_key),
                                                               RangeKey(self.range_key),
                                                               ],
                                                               throughput={'read':self.read_units,'write':self.write_units})
            
        return self.table
    
    
    def put(self, hash_key, range_key, data):
        '''
        puts the data to the table
        if key/range_key exists
        
        '''
        if settings.DEBUG:
            bench_start = time()
        
        data[self.hash_key] = hash_key
        data[self.range_key] = range_key
        
        item = self.table.put_item( data=data, overwrite=True )
        
        if settings.DEBUG:
            
            if not hash_key in self.counters:
                self.counters[hash_key] = {'reads':0,'writes':0}
            self.counters[hash_key]['writes'] +=1
            self.counters['writes'] +=1
            
            elapsed_time = time() - bench_start
            logger.info(data)
            logger.info("R%sW%s - write %0.5f seconds" % (self.counters[hash_key]['reads'], self.counters[hash_key]['writes'], elapsed_time))
        
        return item
        
    
    def get_latest(self, hash_key ):
        '''
        retreive the last recorded data hash_key item for the hash key
        
        '''
        if settings.DEBUG:
            bench_start = time()
        
        kwargs = {}
        kwargs[self.hash_key+'__eq'] = hash_key
        kwargs['limit'] = 1
        
        items = self.table.query( **kwargs )
        
        if items:
            data = {}
            for item in items:
                for key in item.keys():
                    if not key in (self.hash_key, self.range_key):
                        data[key] = item[key]
        else:
            return None
        
        if not len(data):
            return None
        
        if settings.DEBUG:
            
            if not hash_key in self.counters:
                self.counters[hash_key] = {'reads':0,'writes':0}
            self.counters[hash_key]['reads'] +=1
            self.counters['reads'] +=1
            elapsed_time = time() - bench_start
            
            logger.info("R%sW%s - %s - read %0.5f seconds" % (self.counters[hash_key]['reads'], self.counters[hash_key]['writes'], hash_key, elapsed_time))
            
        return data
    
    
    
    def get_range_obj(self, hash_key):
        
        if settings.DEBUG:
            bench_start = time()
        
        kwargs = {}
        kwargs[self.hash_key+'__eq'] = hash_key
        
        # TODO - use batch_get
        items = self.table.query( **kwargs )
        self.counters['reads'] +=1
        data = {}
        
        
        for item in items:
                        
            rkey_data = {}
            rkey = item[self.range_key]
            
            if rkey == 'index':
                data = load_json(item['value'])
                break
            else:
                for key in item.keys():
                    if key != None and not key in (self.hash_key, self.range_key) and key != 'index':
                        if key == 'value':
                            value = item[key]
                            try:
                                rkey_data = load_json(str(value))
                            except:
                                rkey_data = value
                        
                    #else:
                    #    rkey_data[key] = item[key]
                    
            data[rkey] = rkey_data
        
        if settings.DEBUG:
            
            if not hash_key in self.counters:
                self.counters[hash_key] = {'reads':0,'writes':0}
            self.counters[hash_key]['reads'] +=1
            self.counters['reads'] +=1
            
            elapsed_time = time() - bench_start
            #logger.info(data)
            logger.info("R%sW%s - %s - read %0.5f seconds" % (self.counters[hash_key]['reads'], self.counters[hash_key]['writes'], hash_key, elapsed_time))
        
        
        return data
        
    
    def set_range_obj(self, hash_key, data, range_keys=None):
        
        # avoid crashing on attempt to write None data
        if data == None:
            return
        
        if range_keys == None:
            range_keys = data.keys()
        
        # TODO
        # add better size estimate
        
        datablocks = 0
        for range_key in data.keys():
            try:
                len_size = len( data[range_key] )
            except:
                len_size = 1
            datablocks += len_size
        
        # update date in msecs since epoch
        update_date = time()
        
        if datablocks > 1000:
            
            # split over multiple items by data dict key
            with self.table.batch_write() as batch:
                
                for range_key in range_keys:
                    
                    value = json.dumps( data[range_key] )
                    
                    batch_data = {}
                    batch_data[self.hash_key] = hash_key
                    batch_data[self.range_key] = range_key
                    batch_data['value'] = value
                    batch_data['update_date'] = update_date
                    
                    batch.put_item(data=batch_data)
                    
                self.counters['batch_w'] +=1
            
            # delete index if exists
            self.remove_range_obj(hash_key, range_keys=['index'])
            
        else:
            value = json.dumps(data)
            
            batch_data = {}
            batch_data[self.hash_key] = hash_key
            batch_data[self.range_key] = 'index'
            batch_data['value'] = value
            batch_data['update_date'] = update_date
            
            self.table.put_item(data=batch_data, overwrite=True)
            
        self.counters['writes'] +=1
        
        return True
        
    def remove_range_obj(self, hash_key, range_keys=None):
        '''
        deletes ranged object or specific range_keys
        '''
        
        # get range object
        if range_keys == None:
            data = self.get_range_obj(hash_key)
            range_keys = data.keys()
        
        # remove possible index
        try:
            kwargs = {}
            kwargs[self.hash_key] = hash_key
            kwargs[self.range_key] = 'index'
            
            self.table.delete_item( **kwargs )
        except:
            pass
        
        with self.table.batch_write() as batch:
            for range_key in range_keys:
                kwargs = {}
                kwargs[self.hash_key] = hash_key
                kwargs[self.range_key] = range_key
                batch.delete_item( **kwargs )
        
        self.counters['delete'] +=1
        
        return True
    
    
    
class DynamoStorage():
    '''
    Drilldown dynamodb autmatic key/type/value store
    '''
    prefix = ''
    
    is_locked = False
    modified_keys = []
    deleted_keys = []
    
    counts = {'exists':0,'read':0,'write':0,'delete':0,'total':0}
    cached = {'exists':0,'read':0,'write':0,'delete':0,'total':0}
    # 
    def __init__(self, mem_storage, dynamo_table):
        self.values = mem_storage
        self.dynamo_table = DynamoTable( dynamo_table, 'dpath', 'dtype', [], 15, 8 )
    
    #
    def has_key(self, key):
        
        if self.values.has_key(key):
            self.cached['exists']+=1
            return True
        else:
            # ask for key in nosql
            # we store the item in cache to avoid recall
            try:
                self.counts['exists']+=1
                data = self.dynamo_table.get_range_obj(key)
                if data:
                    self.values.set_key_data(key,data)
                    return True
                else:
                    return False
            except:
                return False
    
    
    def get_key_data(self,key):
        
        self.cached['exists']+=1
        if self.values.has_key(key):
            self.cached['read']+=1
            return self.values.get_key_data(key)
        else:
            # ask for key in nosql
            data = self.dynamo_table.get_range_obj(key)
            self.counts['read']+=1
            # assign cache
            self.values.set_key_data(key,data)
            return data
        
    def set_key_data(self,key,value):
        
        if self.is_locked:
            # update the cache
            self.values.set_key_data(key, value)
            # assign to modified keys
            if not key in self.modified_keys:
                self.modified_keys.append(key)
            # remove the key from deleted
            if key in self.deleted_keys:
                self.deleted_keys.remove(key)
            return
        
        # update cache first
        self.values.set_key_data(key, value)
        self.cached['write']+=1
        
        #
        data = self.values.get_key_data(key)
        if data == None:
            range_keys = None
        else:
            range_keys = []
            for k in value:
                if not k in data:
                    range_keys.append(k)
                elif data[k] != value[k]:
                    range_keys.append(k)
        
        # save async to nosql
        self.counts['write']+=1
        return self.dynamo_table.set_range_obj(key, value, range_keys)
        

    def remove_key_data(self,key):
        
        if self.is_locked:
            # remove key from cache
            # self.values.remove_key_data(key)
            # assign to deleted keys
            if not key in self.deleted_keys:
                self.deleted_keys.append(key)
            # remove from modified keys
            if key in self.modified_keys:
                self.modified_keys.remove(key)
            
            return
        
        if self.values.has_key(key):
            range_keys = self.values.get_key_data(key).keys()
        else:
            range_keys = None
        
        # send to nosql first
        self.dynamo_table.remove_range_obj(key,range_keys)
        self.counts['delete']+=1
        # update cache
        self.values.remove_key_data(key)
        self.cached['delete']+=1

    def lock(self):
        '''
        prevent other indexing operations on this table
        '''
        # prevent sending changes to nosql
        self.is_locked = True
        self.dynamo_table.set_range_obj('drilldown-lock', {'date':'now'})
    
    
    def flush(self):
        '''
        release the modified and deleted keys queued for this table
        '''
        # remove deleted keys
        for key in self.deleted_keys:
            self.values.remove_key_data(key)
            self.dynamo_table.remove_range_obj(key)
            time.sleep(0.5)
            if settings.DEBUG:
                logger.debug('removed')
        
        self.deleted_keys = []
        
        # store modified changes
        for key in self.modified_keys:
            # save data by assigning from cached
            data = self.values.get_key_data(key)
            self.dynamo_table.set_range_obj(key, data)
            time.sleep(0.5)
            if settings.DEBUG:
                logger.debug('updated '+key)
        
        self.modified_keys = []
        
        self.dynamo_table.remove_range_obj('drilldown-lock')
        self.is_locked = False
        
    def has_lock(self):
        try:
            drilldown_lock = self.dynamo_table.get_range_obj('drilldown-lock')
            if drilldown_lock:
                return True
            else:
                return False
        except:
            traceback.print_exc()
            return False
        
    
    def print_stats(self):
        
        if settings.DEBUG:
            
            count_exists = self.data_map.cached['exists']
            count_read = self.data_map.cached['read']
            count_write = self.data_map.cached['write']
            count_del = self.data_map.cached['delete']
            
            logger.debug('CACHE: E:'+str(count_exists)+'-R:'+str(count_read)+'-W:'+str(count_write)+'-D:'+str(count_del))
            
            count_exists = self.data_map.counts['exists']
            count_read = self.data_map.counts['read']
            count_write = self.data_map.counts['write']
            count_del = self.data_map.counts['delete']
            
            logger.debug('STATS: E:'+str(count_exists)+'-R:'+str(count_read)+'-W:'+str(count_write)+'-D:'+str(count_del))
            
            count_read = self.data_map.dynamo_table.counters['reads']
            count_write = self.data_map.dynamo_table.counters['writes']
            count_del = self.data_map.dynamo_table.counters['delete']
            
            logger.debug('NOSQL: R:'+str(count_read)+'-W:'+str(count_write)+'-D:'+str(count_del) )