'''
Created on 28 fevr. 2016

@author: biodigitals
'''
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect

from apetizer.models import get_new_uuid, Item
from apetizer.parsers.markdown import item_to_markdown, markdown_to_item
from apetizer.storages.notebook import get_or_create_notebook, save_notebook
from apetizer.views.content import ContentView


class NotebookView(ContentView):
    
    view_name = 'notebook'
    class_actions = ['push','pull',]
    class_action_templates = {'push':'notebook/push.html',
                              'pull':'notebook/pull.html',
                              }
    class_actions_forms = {}
    
    
    def process_push(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Set the notebook to articles
        """
        node = kwargs['node']
        nb = get_or_create_notebook(node)
        
        i = 0
        # if not, create one
        for cell in nb.cells:
            # check for item corresponding
            try:
                cell_id = cell.metadata.gid
            except:
                cell.metadata.gid = get_new_uuid()
                cell_id = cell.metadata.gid
            
            try:
                cell_node = Item.objects.get(id=cell_id)
            except ObjectDoesNotExist:
                cell_node = Item(id=cell_id, parent=node, **kwargs['pipe'])
            
            if cell.cell_type == 'code':
                #
                content = u''
                for output in cell.outputs:
                    if output.output_type == 'stream' and 'stream' == 'stdout':
                        content += output.get('text', u'')
                cell_node.content = content
                
                #if cell_node.content:
                #    cell_node.visible = True
                #else:
                cell_node.visible = False
                
                #if not cell_node.title:
                #    cell_node.title = 'Code'
                
                #if not cell_node.label:
                #    cell_node.label = cell_node.title
                
            elif cell.cell_type == 'markdown':
                
                #cell_node.behavior = 'view'
                #cell_node.content = '<i>markdown rendered html</i>'
                
                cell_node.visible = True
                
                cell = markdown_to_item(cell_node, ''.join(cell.source))

            cell_node.status = 'pushed'
            cell_node.order = i
            cell_node.save()
            i += 1

        save_notebook(nb, node)
        
        #
        if not node.file:
            node.file = 'resource/'+node.id+'.ipynb'
            node.save()
        
        return HttpResponseRedirect(node.get_url()+'view/')

        return self.manage_item_pipe(request, user_profile, input_data, template_args, **kwargs)



    def process_pull(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Set the articles to notebook
        """
        # get or create the notebook
        node = kwargs['node']
        
        nb = get_or_create_notebook(node)

        # create a map of mkdown cell by id
        cell_ids = {}
        for cell in nb.cells:
            if cell.cell_type == 'markdown':
                if hasattr(cell.metadata, 'gid'):
                    cell_ids[cell.metadata.gid] = cell

        for c in node.get_children():
            if c.id in cell_ids:
                cell_ids[c.id].source = item_to_markdown(c)
            else:
                # add a new cell
                nb.cells.append({'cell_type':'markdown',
                                 'source':item_to_markdown(c),
                                 'metadata':{'gid':c.id,
                                             'label':c.label,
                                             'title':c.title}
                                 })
        
        save_notebook(nb, node)
        
        #
        if not node.file:
            node.file = 'resource/'+node.id+'.ipynb'
            node.save()
        
        return HttpResponseRedirect(node.get_url()+'file/')
        
        return self.manage_item_pipe(request, user_profile, input_data, template_args, **kwargs)
        
    

