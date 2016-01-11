'''
Created on 28 dec. 2015

@author: biodigitals
'''
from apetizer.forms.program import ProgramEditForm
from apetizer.views.content import ContentView


class ProgramView(ContentView):
    
    view_name = 'program'
    
    class_actions = ['program','call']
    
    class_action_templates = {'program':'apetizer/program.html',
                              'call':'apetizer/program.html'}
    
    class_actions_forms = {'program':(ProgramEditForm,),
                           'call':(ProgramEditForm,)}
    
    def process_program(self, request, user_profile, input_data,
                      template_args, **kwargs):
        
        
        # check if there is a py file
        # if not create one ...
        # load the grid
        
        # filter by table, row, col, page
        # apply posted changes ?
        # build the html table view
        # save the program if modified
        
        template_args['tables'] = [('macros',[
                                             (0,1,2,3),
                                             (1,2,3,4)
                                            ])]
        
        
        return self.manage_pipe(request, user_profile, input_data, template_args, **kwargs)
    
    def process_call(self, request, user_profile, input_data,
                      template_args, **kwargs):
        # check if there is a py file
        # if not create one ...
        # load the grid
        
        # filter by table, row, col, page
        # execute the selection
        template_args['tables'] = [('macros',[
                                             (0,1,2,3),
                                             (1,2,3,4)
                                            ])]
        return self.manage_pipe(request, user_profile, input_data, template_args, **kwargs)
    


    def process_import(self, request, user_profile, input_data,
                      template_args, **kwargs):
        return self.manage_pipe(request, user_profile, input_data, template_args, **kwargs)
    
    def process_export(self, request, user_profile, input_data,
                      template_args, **kwargs):
        return self.manage_pipe(request, user_profile, input_data, template_args, **kwargs)
    
    
    
    def process_listen(self):
        return
    
    def process_dispatch(self):
        return
    
    def process_tell(self):
        return
    
