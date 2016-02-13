'''
Created on 25 janv. 2016

@author: nicolas
'''
import threading


global _core
_core = None

class Core(dict):
    wsockets = []

#
class CoreManager():
    
    _core = None
    _core_lock = threading.Lock()
    
    def __unicode__(self):
        return self.name
    
    @classmethod
    def get_core(cls):
        with cls._core_lock:
            if cls._core == None:
                cls._core = Core()
        return cls._core


    @classmethod
    def get_root(cls, name='localhost'):
        R = {'id':name}
        return R

    @classmethod
    def get_user(cls, user_id):
        U = {'id':user_id}
        return U
    
    @classmethod
    def get_session(cls, session_key):
        S = {'id':session_key}
        return S

