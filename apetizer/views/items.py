'''
Created on 28 fevr. 2016

@author: biodigitals
'''
from apetizer.forms.items import ItemCutForm, ItemCopyForm, ItemPasteForm
from apetizer.models import Moderation, Item
from apetizer.views.content import ContentView


class ItemView(ContentView):
    """
    TODO
    
    Implement this logic
    
    and insert uid copy from pages
    """
    
    view_name = 'item'
    view_template = "ui/base.html"
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
        
        # generate a moderation indicating the item will be cutted
        cut_markup = Moderation(**kwargs['pipe'])
        cut_markup.related_id = kwargs['node'].id
        cut_markup.status = 'cutting'
        cut_markup.save()
        
        return self.manage_item_pipe(request, user_profile, input_data, template_args, **kwargs)

    def process_copy(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Copy an item to paste it somewhere else

        takes a uid as parameter and
        returns the one of the copy
        """
        
        # generate a moderation indicating the item will be copied
        cut_markup = Moderation(**kwargs['pipe'])
        cut_markup.related_id = kwargs['node'].id
        cut_markup.status = 'copying'
        cut_markup.save()
        
        return self.manage_item_pipe(request, user_profile, input_data, template_args, **kwargs)

    def process_paste(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Paste an item somewhere

        takes a uid as parameter and set's the item's parent to current node
        """
        
        # clear the markups
        paste_markups = Moderation.objects.filter(akey=user_profile.akey, 
                                                  visible=True,
                                                  action__in=('cut', 'copy'), 
                                                  status__in=('cutting', 'copying'), 
                                                  ).order_by('-ref_time')
        
        if paste_markups.count():
            # manage the first as it is the last geenrated markup
            markup = paste_markups[0]
            if markup.status == 'cutting':
                markup.related.parent = kwargs['node']
                markup.related.save()
                markup.status = 'cutted'
                markup.save()
            
            elif markup.status == 'copying':
                # create a clone
                item = Item(**markup.related.get_as_dict())
                item.parent = kwargs['node']
                item.status = 'copied'
                item.save()
                markup.status = 'copied'
                markup.save()
            
            # clear the markups
            for markup in paste_markups:
                markup.visible = False
                markup.save()
            
        return self.manage_item_pipe(request, user_profile, input_data, template_args, **kwargs)
                    
    


