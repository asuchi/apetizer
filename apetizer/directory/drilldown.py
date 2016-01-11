'''
Created on 11 fev. 2014

@author: rux
'''

from collections import OrderedDict
from math import radians, cos, sin, asin, sqrt


class Drilldown():
    
    indexes = { 'type': {'name':('id')} }
    object_types = {}
    
    # id
    # value 
    #    - ids
    #    - values
    
    def __init__(self, index_map, data_map=None, object_map=None):
        
        if data_map != None:
            self.data_map = data_map
        else:
            self.data_map = {}
        
        if object_map != None:
            self.object_map = object_map
        else:
            self.object_map = {}
        
        # verify all index keys are unicode
        self.indexes = {}
        for otype in index_map:
            self.indexes[unicode(otype)] = {}
            for index_key in index_map[otype]:
                self.indexes[unicode(otype)][unicode(index_key)] = []
                for index_value in index_map[otype][index_key]:
                    self.indexes[unicode(otype)][unicode(index_key)].append(index_value)
        
        self.prepare()
        
    def prepare(self):
        # override this method is here to load initial data
        pass
    
    def get_key_data(self,key):
        return self.data_map.get_key_data(key)
    
    def has_key(self,key):
        return self.data_map.has_key(key)
    
    
    def guess_type_from_data(self, path):
        
        path_key_type = None

        path_key_data = self.data_map.get_key_data(path)
        for key in ('country','region','dept','town','type','town-make','dept-make','make','dept-type','town-type','town-make-model'):
            if key in path_key_data and len(path_key_data[key]) == 1:
                if path in path_key_data[key].keys():
                    path_key_type = key
                    break
        
        if path_key_type == None:
            max_count = 0
            # if key have diverged, guess by using the highest count
            for key in ('country','region','dept','town','type','town-make','dept-make','make','dept-type','town-type','town-make-model'):
                if key in path_key_data and path in path_key_data[key]:
                    if path in path_key_data[key].keys():
                        count = self.get_object_key_count( path, key )
                        if count > max_count:
                            path_key_type = key
        
        return path_key_type
    
    def get_object_key_count(self, slug, obj_type):
        
        if self.has_key(slug) \
            and obj_type in self.get_key_data(slug).keys():
            
            return  self.get_key_data(slug)[obj_type][slug]
        else:
            return self.get_object(obj_type, slug)['count']
    
    def has_object(self, object_type, key):
        key = unicode(key)
        return self.object_map.has_key( unicode(object_type+'-'+key) )
    
    def get_object(self, object_type, key):
        key = unicode(key)
        return self.object_map.get_key_data( unicode(object_type+'-'+key) )
    
    def set_object(self, object_type, key, data):
        key = unicode(key)
        return self.object_map.set_key_data( unicode(object_type+'-'+key), data )
    
    def add_object(self, obj_type, obj):
        
        clean_data = {}
        
        # clean input data
        for k in obj.keys():
            
            if obj[k] == None:
                obj[k] = 'none'
            
            elif obj[k] == '' or obj[k] == u'':
                obj[k] = 'empty'
            
            if type(obj[k]) == type(0):
                obj[k] = unicode(str(obj[k]))
            
            if type(obj[k]) == type(''):
                obj[k] = unicode(str(obj[k]))
            
            clean_data[unicode(k)] = obj[k]
        
        obj = clean_data
        
        if not obj_type in self.object_types:
            self.object_types[obj_type] = []
        
        keys_modified = []
        
        # register object data
        if not self.has_object(obj_type,clean_data[obj_type]):
            # duplicate base with type prefix
            obj_map_key_dict = OrderedDict()
        else:
            obj_map_key_dict = self.get_object(obj_type,clean_data[obj_type])
        
        if not 'stats' in obj_map_key_dict:
            obj_map_key_dict[u'stats'] = {'count':1}
        
        if not 'data' in obj_map_key_dict:
            obj_map_key_dict[u'data'] = clean_data
            if obj_type in self.indexes:
                obj_map_key_dict[u'indexes'] = self.indexes[obj_type]
            else:
                obj_map_key_dict[u'indexes'] = []
        else:
            obj_map_key_dict[u'stats'][u'count'] += 1
        
        
        object_map_key = obj_type+'-'+clean_data[obj_type]
        
        self.object_map.set_key_data(object_map_key, obj_map_key_dict)
        
        # add data access keys mashup
        if obj_type in self.indexes:
            
            for okey in clean_data.keys():
                
                if okey in obj_map_key_dict[u'indexes']:
                    
                    object_keys = obj_map_key_dict[u'indexes'][okey]
                    
                    data_key = clean_data[okey]
                    
                    # test if data object key exists
                    if not self.data_map.has_key(data_key):
                        data_obj = OrderedDict()
                    else:
                        data_obj = self.data_map.get_key_data(data_key)
                    
                    # for each index keys
                    for key in object_keys:
                        
                        key = unicode(key)
                        
                        if key in clean_data.keys():
                            
                            # test if index key exists and create dict
                            if not key in data_obj.keys():
                                data_obj[key] = OrderedDict()
                            
                            # if key isn't registred do so
                            if not clean_data[key] in data_obj[key].keys():
                                data_obj[key][ clean_data[key] ] = 1
                            else:
                                data_obj[key][ clean_data[key] ] += 1
                    
                    if not data_key in keys_modified:
                        keys_modified.append(data_key)
                    
                    # save modified data index
                    self.data_map.set_key_data( data_key, data_obj )
                    
        #print keys_modified
        
        return keys_modified

    def remove_object(self, obj_type, object_key):
        
        obj_type = unicode(obj_type)
        obj_map_key_dict = self.object_map.get_key_data( obj_type+'-'+unicode(object_key) )
        
        if 'indexes' in obj_map_key_dict:
            indexes = obj_map_key_dict[u'indexes']
            
        elif obj_type in self.indexes:
            indexes = self.indexes[obj_type]
        
        else:
            indexes = []
        
        obj = obj_map_key_dict[u'data']
        
        # for each data key
        for okey in obj.keys():
            
            data_key = obj[okey]
            data_obj = self.data_map.get_key_data( data_key )
            
            data_modified = False
            
            # if there is an index setup for the data key
            if len(indexes):
                # if the objet data key is in the indexes
                if okey in indexes:
                    
                    object_keys = indexes[okey]
                    
                    # for each key in index
                    for key in object_keys:
                        
                        if key in obj.keys():
                            
                            # test if data_key exists
                            if key in data_obj.keys():
                                
                                # decrement data-key count
                                if obj[key] in data_obj[key].keys():
                                    data_obj[key][ obj[key] ] -= 1
                                    data_modified = True
                                    # remove data key if count is 0
                                    if data_obj[key][ obj[key] ] == 0:
                                        del data_obj[key][ obj[key] ]
                                        data_modified = True
                                
                                # remove key if no more indexes in
                                if len(data_obj[key].keys()) == 0:
                                    del data_obj[key]
                                    data_modified = True
            
            if data_modified:
                if len(data_obj.keys()) == 0:
                    self.data_map.remove_key_data(data_key)
                else:
                    self.data_map.set_key_data( data_key, data_obj )
        
        #
        obj_map_key_dict[u'stats'][u'count'] -= 1
        if obj_map_key_dict[u'stats']['count'] <= 0:
            # remove object
            self.object_map.remove_key_data( obj_type+'-'+object_key )
        
            
    def add_to_ranking(self, object_type, slug, ranking ):
        pass
    
    
    def add_to_bounds(self, object_type, slug, lat, lng):
        
        obj_type_slug = object_type+'-'+slug
        
        lat = float(lat)
        lng = float(lng)
        
        if self.object_map.has_key(obj_type_slug):
            
            obj_map = self.object_map.get_key_data(obj_type_slug)
            
            obj_type_map = obj_map['stats']
            
            bounds_changed = False
            if not u'bounds' in obj_type_map:
                obj_type_map[u'bounds'] = [lat,lng,lat,lng]
                bounds_changed = True
            
            if not 'prev_bounds' in obj_type_map:
                obj_type_map['prev_bounds'] = [[],[],[],[]]
            
            bounds = obj_type_map[u'bounds']
            prev_bounds = obj_type_map['prev_bounds']
            
            # left top
            if lat < bounds[0]:
                prev_bounds[0].insert(0,bounds[0])
                bounds[0] = lat
                bounds_changed = True
            elif lat == bounds[0]:
                prev_bounds[0].insert(0,bounds[0])
                bounds_changed = True
                
            if lng > bounds[1]:
                prev_bounds[1].insert(0,bounds[1])
                bounds[1] = lng
                bounds_changed = True
            elif lng == bounds[1]:
                prev_bounds[1].insert(0,bounds[1])
                bounds_changed = True
                
            # right bottom
            if lat > bounds[2]:
                prev_bounds[2].insert(0,bounds[2])
                bounds[2] = lat
                bounds_changed = True
            elif lat == bounds[2]:
                prev_bounds[2].insert(0,bounds[2])
                bounds_changed = True
                
            if lng < bounds[3]:
                prev_bounds[3].insert(0,bounds[3])
                bounds[3] = lng
                bounds_changed = True
            elif lng == bounds[3]:
                prev_bounds[3].insert(0,bounds[3])
                bounds_changed = True
                
            if bounds_changed:
                obj_type_map[u'lat'] = (bounds[0]+bounds[2])/2.0
                obj_type_map[u'lng'] = (bounds[1]+bounds[3])/2.0
                obj_type_map[u'bounds'] = bounds
                obj_type_map[u'prev_bounds'] = prev_bounds
                obj_type_map[u'radius'] = max( int( haversine( bounds[0],bounds[1],bounds[2],bounds[3] )*1000/2 ), 800 )
                
                # calculate geohash
                #obj_type_map[u'geohash'] = ''
                
                obj_map['stats']=obj_type_map
                
                self.object_map.set_key_data(obj_type_slug, obj_map)

    def remove_from_bounds(self, object_type, slug, lat, lng):
        
        obj_type_slug = object_type+'-'+slug
        
        lat = float(lat)
        lng = float(lng)
        
        if self.object_map.has_key(obj_type_slug):
            
            obj_map = self.object_map.get_key_data(obj_type_slug)
            
            obj_type_map = obj_map['stats']
            
            bounds_changed = False
            if not u'bounds' in obj_type_map:
                obj_type_map[u'bounds'] = [lat,lng,lat,lng]
            
            bounds = obj_type_map[u'bounds']
            if not 'prev_bounds' in obj_type_map:
                obj_type_map['prev_bounds'] = [[],[],[],[]]
            
            prev_bounds = obj_type_map[u'prev_bounds']
            
            # left top
            if lat == bounds[0]:
                bounds[0] = prev_bounds[0].pop(0)
                bounds_changed = True
            elif prev_bounds[0].index(lat) >= 0:
                prev_bounds[0].remove(lat)
                bounds_changed = True
                
            if lng == bounds[1]:
                bounds[1] = prev_bounds[1].pop(0)
                bounds_changed = True
            elif prev_bounds[1].index(lng) >= 0:
                prev_bounds[1].remove(lng)
                bounds_changed = True
                
            # right bottom
            if lat == bounds[2]:
                bounds[2] = prev_bounds[2].pop(0)
                bounds_changed = True
            elif prev_bounds[2].index(lat) >= 0:
                prev_bounds[2].remove(lat)
                bounds_changed = True
                
            if lng == bounds[3]:
                bounds[3] = prev_bounds[3].pop(0)
                bounds_changed = True
            elif prev_bounds[3].index(lng) >= 0:
                prev_bounds[3].remove(lng)
                bounds_changed = True
            
            if bounds_changed:
                
                radius = max( int( haversine( bounds[0],bounds[1],bounds[2],bounds[3] )*1000/2 ), 800 )
                
                obj_type_map[u'lat'] = (bounds[0]+bounds[2])/2.0
                obj_type_map[u'lng'] = (bounds[1]+bounds[3])/2.0
                
                obj_type_map[u'bounds'] = bounds
                obj_type_map[u'prev_bounds'] = prev_bounds
                
                obj_type_map[u'radius'] = radius
                
                # calculate geohash
                #obj_type_map[u'geohash'] = ''
                
                obj_map['stats'] = obj_type_map
                
                self.object_map.set_key_data(obj_type_slug, obj_map)
        
        
            
    def get_closest(self, lat, lng, obj_type):
        
        # get the geohash
        
        # request for it
        
        pass




# http://stackoverflow.com/questions/4913349/haversine-formula-in-python-bearing-and-distance-between-two-gps-points

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 

    # 6367 km is the radius of the Earth
    km = 6367 * c
    return km 



# exemple drilldown view
# 
