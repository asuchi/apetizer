'''
Created on Feb 13, 2015

@author: nicolas
'''
from pystory.scenario.nodes import ScenarioNode

from apetizer.views.actionpipe import ActionPipeView


class ActionPipeScenarioNode(ScenarioNode):
    
    def __init__(self, parent, form, field, view, action, node, func, value, **kwargs):
        
        cls = form.__class__
        
        form_field = form
        #ScenarioNode.__init__(self, parent, cls, key, func, value, ref, target, method)
        
        return


if __name__ == '__main__':
    # string, class, action
    
    # form field
    # form
    # model field
    # pipe class
    # model.field
    class RegisterView(ActionPipeView):
        
        def __init__(self, **kwargs):
        
            ActionPipeView.__init__(self, **kwargs)
            
            # Check email to see if user known.
            ActionPipeScenarioNode(self, cls=LoginInfosForm, key='email', view=self.__class__, action='login'),
            
            # check for first name, last name
            ActionPipeScenarioNode(self, cls=RegisterInfosForm, key='first_name', action='infos')
            ActionPipeScenarioNode(self, cls=RegisterInfosForm, key='last_name', action='infos')
            
            ActionPipeScenarioNode(self, key='user_registred', action='save')
            
            # check for user choice to register as owner or driver
            gender = ActionPipeScenarioNode(self, form=RegisterInfosForm, field='gender', action='infos')
            
            #
            ActionPipeScenarioNode(self, ref=gender, func='__eq__', value='owner', cls=self.data, key='user_registred', view=RegisterView, action='infos')
            ActionPipeScenarioNode(self, ref=gender, func='__eq__', value='driver', cls=self.data, key='user_registred', view=RegisterView, action='infos')
            
            ActionPipeScenarioNode(self, ref=gender, func='__eq__', value=None, cls=RegisterInfosForm, key='first_name', view=self, method=('infos'), )
            #
        
