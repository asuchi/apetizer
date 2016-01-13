'''
Created on 12 janv. 2016

@author: biodigitals
'''
import json

from apetizer.forms.semantic import SemanticDescribeForm, SemanticEditForm
from apetizer.views.content import ContentView


class SemanticView(ContentView):
    
    class_actions = ['describe', 'edit']
    
    class_action_templates = {'describe':'semantic/describe.html',
                              'edit':'semantic/edit.html',}
    
    
    class_actions_forms = {'describe':(SemanticDescribeForm,),
                          'edit':(SemanticEditForm,),
                          }
    
        
    def process_describe(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Edit the item class
        
        the ontology of the class corresponds to the item root node url
        
        
        """
        item = kwargs['node']
        
        class_attributes = item.get_data().get('attributes',[])
        
        if input_data.get('attribut_name') and input_data.get('attribut_type'):
            class_attributes.append({'name':input_data.get('attribut_name'),
                                     'type':input_data.get('attribut_type') })
        
            data = item.get_data()
            data['attributes'] = class_attributes
            
            item.set_data(data)
            item.save()
        
        template_args['class_attributes'] = class_attributes
        
        return self.manage_pipe(request, user_profile, input_data, template_args, **kwargs)
    

    def process_edit(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Edit an item instance
        
        item must have type from ontology class
        
        if it's ok, creates an instance or deletes the instance on all empty data posted
        
        """
        item = kwargs['node']
        
        class_attributes = item.get_data().get('properties',[])
        
        if input_data.get('attribut_name') and input_data.get('attribut_value'):
            class_attributes.append({'name':input_data.get('attribut_name'),
                                     'value':input_data.get('attribut_value') })
        
            data = item.get_data()
            data['properties'] = class_attributes
            
            item.set_data(data)
            item.save()
        
        template_args['class_attributes'] = class_attributes
        
        return self.manage_pipe(request, user_profile, input_data, template_args, **kwargs)


        
        
        