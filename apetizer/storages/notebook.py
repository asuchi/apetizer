'''
Created on 26 fevr. 2016

@author: biodigitals
'''
from datetime import datetime
import io
import json
import os
#from IPython.nbformat import current, NotebookNode, validate

class Notebook(object):
    def __init__(self, **entries): 
        self.__dict__.update(entries)
        print(entries)

def get_or_create_notebook(node):
    
    fname = os.getcwd()+'/resource/'+node.id+'.ipynb'
    ## is there a file ?
    if not os.path.exists(fname):
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
    fname = os.getcwd()+'/resource/'+node.id+'.ipynb'
    # write changes
    with io.open(fname, 'w', encoding='utf-8') as f:
        f.write(json.dumps(nb, default=API_json_parser).decode('utf-8'))
        f.close()
