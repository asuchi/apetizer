'''
Created on 22 janv. 2016

@author: biodigitals
'''

def unicode3(value, *args, **kwargs):
    """
    Rewire of the unicode function for python 3 support
    """
    try:
        import __builtin__
        __builtin__.unicode(value, *args **kwargs)
    except:
        return value