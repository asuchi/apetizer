'''
Created on 25 sept. 2015

@author: biodigitals
'''

from django.forms.models import model_to_dict

from apetizer.models import DataPath
from apetizer.parsers.api_json import load_json, dump_json


class ModelIndex():
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




class ModelStore(ModelIndex):
    """
    Key value store for action pipe data
    """
    data = {}
    model = DataPath
    
    hash_key = 'akey'
    range_key = 'action'

    def put(self, hash_key, range_key, data):
        
        try:
            params = {}
            params[self.hash_key] = hash_key
            params[self.range_key] = range_key
            #data_object = self.model.objects.filter(**params).order_by('-ref_time')[0]
            data_object = self.model.objects.filter(akey=hash_key, action=range_key, completed_date__isnull=True).order_by('-ref_time')[0]
            for key in data.keys():
                if key == 'data':
                    data_object.__setattr__(key, dump_json(data[key]))
                else:
                    data_object.__setattr__(key, data[key])
            
            data_object.full_clean()
            data_object.save()
        
        except IndexError:
            
            if not self.range_key in data:
                data[self.range_key] = range_key
            
            data_keys = data.keys()
            for key in data_keys:
                if key.endswith('_ptr'):
                    del data[key]
            
            new_object = self.model(**data)
            
            # should check for matching hash_key/range_key
            new_object.akey = hash_key
            new_object.action = range_key
            
            #
            new_object.data = dump_json(new_object.data)
            
            #
            new_object.full_clean()
            new_object.save()

    def get_latest(self, hash_key, range_key=None):
        try:
            if range_key:
                data_obj = self.model.objects.filter(akey=hash_key, action=range_key, completed_date__isnull=True).order_by('-ref_time')[0]
            else:
                data_obj = self.model.objects.filter(akey=hash_key, completed_date__isnull=True).order_by('-ref_time')[0]
            
            pipe_data = self.get_default_obj_data()
            
            obj_data = model_to_dict(data_obj)
            
            pipe_data.update(obj_data)
            pipe_data['data'] = load_json(data_obj.data)
            
            #try:
            #    pipe_data['data'] = json.loads(data_obj.data)
            #except:
            #    traceback.print_exc()
            #    pipe_data['data'] = {}
            #pipe_data['data'] = deepcopy(data_obj.data)
            return pipe_data
        
        except IndexError:
            return None
    
    def get_default_obj_data(self):
        return {}
    
    def get_range_obj(self, hash_key):
        rkeys = self.model.objects.filter(akey=hash_key)
        range_list = []
        for rkey in rkeys:
            range_list.append(load_json(rkey.data))
        return range_list

    def set_range_obj(self, hash_key, data, range_keys=None):
        if range_keys:
            for range_key in range_keys:
                self.put(hash_key, range_key, data)
        else:
            # get range keys from existing
            for o in self.get_range_obj(hash_key):
                self.put(hash_key, o.action, data)

    def remove_range_obj(self, hash_key, range_keys=None):
        if range_keys == None:
            self.model.objects.filter(akey=hash_key).delete()
        else:
            for range_key in range_keys:
                self.model.objects.filter(akey=hash_key, action=range_key).delete()

