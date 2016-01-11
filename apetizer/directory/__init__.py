'''
Created on 7 oct. 2013

@author: rux
'''
# local memory cache for default search forms
from apetizer.storages.memcached import DictStorage, MemcacheStorage
from apetizer.storages.kvstore import KVStore
global _search_forms
_search_forms = {}

# temp local memory caches for search key between cache flushes
global _session_search_keys
_session_search_keys = {}

global _search_keys
_search_keys = {}

global _search_key_points
_search_key_points = {}


# local memory caches for results
global _search_key_sort_results
_search_key_sort_results = {}

global _search_key_page_results
_search_key_page_results = {}


# setup
global _history_connector
_history_connector = None

# initialise the connection with dynamodb
# 
table_name = 'skeys'
hash_key = 'skey' # search md5 key
range_key = 'ssid' # user session key
indexes = [] # 

_history_connector = KVStore()
#from apetizer.nosql.dynamodb import DynamoTable
#DynamoTable( table_name, hash_key, range_key, indexes )



