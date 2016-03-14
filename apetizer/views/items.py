'''
Created on 28 fevr. 2016

@author: biodigitals
'''

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect

from apetizer.forms.content import ItemRelatedForm
from apetizer.forms.items import ItemCutForm, ItemCopyForm, ItemPasteForm
from apetizer.models import get_new_uuid, Item
from apetizer.parsers.markdown import item_to_markdown, markdown_to_item
from apetizer.storages.notebook import get_or_create_notebook, save_notebook
from apetizer.views.content import ContentView


class ItemView(ContentView):
    """
    TODO
    
    Implement this logic
    
    and insert uid copy from pages
    """
    
    view_name = 'item'
    class_actions = ['cut', 'copy', 'paste']
    class_action_templates = {}
    class_actions_forms = {'cut':(ItemCutForm,),
                           'copy':(ItemCopyForm,),
                           'paste':(ItemPasteForm,),
                           }

    def process_cut(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Cut an item from the tree to paste it somewhere else

        takes a uid as parameter, 

        hides it and redirect it to an unparented copy
        returns it' uid
        """
        return self.manage_item_pipe(request, user_profile, input_data, template_args, **kwargs)

    def process_copy(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Copy an item to paste it somewhere else

        takes a uid as parameter and
        returns the one of the copy
        """
        return self.manage_item_pipe(request, user_profile, input_data, template_args, **kwargs)

    def process_paste(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Paste an item somewhere

        takes a uid as parameter and set's the item's parent to current node
        """
        return self.manage_item_pipe(request, user_profile, input_data, template_args, **kwargs)
                    
    


