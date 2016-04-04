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
        
        # if the item is flagged as busy
        #    redirect to busy page is done by the business view
        
        # start the module ASYNC
        process = node.call_async()
        # A# lock and set the item as busy
        # A# run
        # A# lock and unset item as busy

        # if it does not complete within 2 seconds
        #   redirect to busy action
        if process:
            run_time = 0
            while process.running:
                run_time += 0.2
                time.sleep(0.2)
                if run_time >= 2:
                    break
        
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
    
