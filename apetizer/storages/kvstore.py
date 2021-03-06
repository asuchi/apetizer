'''
Created on Feb 9, 2015

@author: nicolas
'''


class KVStore(object):
    """
    Key value store for action pipe data
    """
    data = {}

    def put(self, hash_key, range_key, data):
        if hash_key not in self.data:
            self.data[hash_key] = {}
        self.data[hash_key][range_key] = data
        return

    def get_latest(self, hash_key, range_key=None):
        if hash_key in self.data:
            if range_key == None:
                return self.data[hash_key]
            else:
                if range_key in self.data[hash_key]:
                    return self.data[hash_key][range_key]
                else:
                    return self.data[hash_key]
        else:
            return None

    def get_range_obj(self, hash_key):
        o = self.data[hash_key]
        return o

    def set_range_obj(self, hash_key, data, range_keys=None):
        self.data[hash_key] = data
        return

    def remove_range_obj(self, hash_key, range_keys=None):
        del self.data[hash_key]
        return
