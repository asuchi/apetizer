'''
Created on 26 fevr. 2016

@author: biodigitals
'''
import io
import json
import os

from django.conf import settings


class Notebook(object):
    """
    Simple object wrapper for the notebook json data
    """
    def __init__(self, **entries): 
        self.__dict__.update(entries)
        print(entries)

def get_or_create_notebook(node):
    """
    Get or create notebook for the provided node
    
    Should be like:
    
    doc_nb = {
        'content': {
            'cells': [
                {
                    'cell_type': 'markdown',
                    'metadata': {},
                    'source': 'Some **Markdown**',
                },
            ],
            'metadata': {'id':node.id},
            'nbformat': 4,
            'nbformat_minor': 0,
        },
        'created': datetime(2015, 7, 25, 19, 50, 19, 19865),
        'format': 'json',
        'last_modified': datetime(2015, 7, 25, 19, 50, 19, 19865),
        'mimetype': None,
        'name': 'a.ipynb',
        'path': fname,
        'type': 'notebook',
        'writable': True,
    }
    """
    fname = os.path.join(settings.MEDIA_ROOT, node.id+'.ipynb')
    
    ## is there a file ?
    if not os.path.exists(fname):
        
        
        nb = Notebook(
                **{u'metadata': {},
                u'nbformat': 4,
                u'nbformat_minor': 0,
                u'cells': []}
                )
    else:
        # read the file
        with io.open(fname, 'r', encoding='utf-8') as f:
            #nb = current.read(f, 'json')
            nb = json.loads(f.read(), object_hook=API_json_loader)
            f.close()
    
    return nb

def API_json_loader(obj):
    """Default JSON deserializer."""
    return Notebook(**obj)

def API_json_parser(obj):
    """Default JSON serializer."""
    if isinstance(obj, Notebook):
        return obj.__dict__
    else:
        return obj

def save_notebook(nb, node):
    fname = os.path.join(settings.MEDIA_ROOT, node.id+'.ipynb')
    # write changes
    with io.open(fname, 'w', encoding='utf-8') as f:
        f.write(unicode(json.dumps(nb, default=API_json_parser)))
        f.close()
