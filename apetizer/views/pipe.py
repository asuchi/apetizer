'''
Created on 16 mai 2014

@author: rux
'''
from collections import OrderedDict
import copy
import json
import uuid

from django.core.cache import cache as action_cache
from django.forms.models import model_to_dict
from django.http import HttpResponseRedirect
from django.utils.timezone import now
from django.utils.translation import get_language

from apetizer.forms.base import ActionModelForm
from apetizer.models import DataPath
from apetizer.parsers.json import API_json_parser
from apetizer.storages.kvstore import KVStore
from apetizer.views.action import ActionView
from apetizer.views.api import ApiView


__all__ = ['ActionPipeView', ]


class ActionPipeView(ApiView, ActionView):
    '''
    base class for an action pipe view
    '''
    pipe_table = KVStore()

    """
    Default action data dict
    """
    pipe_data_model = {
        # hash_key
        'akey': 'default',
        # range key
        'action': 'undefined', #-> status !
        # second range index
        'path': None,
        'data': json.dumps({}),
    }
    
    pipe_hash_key = 'akey'
    pipe_range_key = 'action'
    
    class_actions = ['prev', 'next', 'reset']
    class_action_templates = {'reset':'register/reset.html'}
    
    pipe_table = KVStore()
    
    action_scenarios = {}
    
    #pipe_scenario = OrderedDict([])
    '''
    pipe_scenario defines a sequence of field names
    that has to be filled by the user to complete the pipe action
    these are mapped to view names
    in order to find the needed view to display
    scenario will run until all flaged data elements are filled with something
    '''
    def __init__(self, *args, **kwargs):
        return super(ActionPipeView, self).__init__(*args, **kwargs)
        #self.pipe_scenario = OrderedDict([('pipe-started',
        #                                   {'class': self.__class__,
        #                                    'action': 'start'}
        #                                   ),
        #                                  ('pipe-finished',
        #                                   {'class': self.__class__,
        #                                    'action': 'finish'}
        #                                   )])

    def get_session_user_keys(self, request):
        """
        Get actionpipe data container key
        Generates a new one if missing cookie
        """
        akey = None
        if request.session.has_key(self.pipe_hash_key):
            akey = request.session[self.pipe_hash_key]
        if not akey:
            akey = request.COOKIES.get(self.pipe_hash_key, None)
            if not akey:
                # generate a new one
                akey = self.get_new_session_user_key()
        
        request.session[self.pipe_hash_key] = akey
        return akey

    def get_new_session_user_key(self):
        return str(uuid.uuid4())


    def get_default_pipe_data(self, request, akey, **kwargs):
        """
        Get a default action data dict
        """
        pipe_data = copy.deepcopy(self.pipe_data_model)
        
        pipe_data[self.pipe_hash_key] = akey
        pipe_data[self.pipe_range_key] = kwargs.get('action')
        
        pipe_data['locale'] = get_language()
        pipe_data['path'] = self.get_referer_path(request)
        pipe_data['data'] = {}
        return pipe_data


    def get_action_cache_key(self, key):
        """
        Get a correct cache key for action data
        """
        return 'ap-'+str(key)
    
    
    def get_action_scenario(self, action):
        """
        Return the scenario for the action
        """
        if not action in self.action_scenarios:
            return {}
        #OrderedDict([])
        
        return self.action_scenarios[action]
    
    def get_user_profile(self, request, **kwargs):
        """
        Retreive user profile from the request user
        """
        user_profile = super(ActionPipeView, self).get_user_profile(request, **kwargs)
        user_profile.update(kwargs['pipe'])
        return user_profile
    
    def pre_process(self, request, input_data, **kwargs):
        """
        Hook before processing the request
        Best place to make user/objects rights management
        """
        # get actual user data
        akey = self.get_session_user_keys(request)
        
        kwargs['pipe'] = self.update_actionpipe_data(request, input_data, akey, **kwargs)
        
        response = super(ActionPipeView, self).pre_process(request, input_data, **kwargs)
        
        return self.finish(request, response, **kwargs)
    
    def process_next(self, request, user_profile, input_data, template_args, **kwargs):
        '''
        call this method to be redirected to the next pipe view
        '''
        next_url = self.get_next_url(kwargs.get('pipe'), **kwargs)
        
        if next_url != '/'+request.path_info:
            return HttpResponseRedirect(next_url)
        else:
            return HttpResponseRedirect(self.get_reversed_action(self.view_name, 'profile', kwargs))

    def process_prev(self, request, user_profile, input_data, template_args, **kwargs):
        '''
        call this method to be redirected to the previous pipe view
        '''
        return HttpResponseRedirect(self.get_prev_url(kwargs.get('pipe'), **kwargs))


    def process_reset(self, request, user_profile, input_data, template_args, **kwargs):
        '''
        Resets the current profile by rotating the akey
        '''
        user_data = kwargs.get('pipe')
        if not input_data.get('token'):
            self.rotate_akey(request, user_data, **kwargs)
            # removing current akey cookie will rotate the key
            return HttpResponseRedirect(self.get_reversed_action(kwargs['view_name'], ActionPipeView.default_action, kwargs))
        else:
            return self.render(request, template_args, **kwargs)
        

    def rotate_akey(self, request, user_data, **kwargs):
        # rotate session akey
        new_akey = self.get_new_session_user_key()
        
        kwargs['pipe'] = self.update_actionpipe_data(request, {}, new_akey, **kwargs)
        kwargs['pipe'] = self.save_actionpipe_data(request, kwargs['pipe'], new_akey, **kwargs)
        
        request.session[self.pipe_hash_key] = new_akey
        return request.session[self.pipe_hash_key]
    
    
    def is_proposal(self, user_profile, instance, **kwargs):
        """
        To override, depends on the model
        """
        return False
    
    
    def create_proposal(self, request, user_profile, input_data, template_args, **kwargs):
        """
        To override, depends on the model
        """
        return self.render(request, template_args, **kwargs)
    
    
    def manage_pipe(self, request, user_profile, input_data, template_args, **kwargs):
        
        action = kwargs['action']
        
        if request.method.lower() == 'get':
            bound_forms = False
        else:
            bound_forms = True
        
        action_forms = self.get_validated_forms(self.get_forms_instances(action, 
                                                                         user_profile,
                                                                         kwargs),
                                                 #kwargs['pipe']['data'],
                                                 input_data,
                                                 action, 
                                                 save_forms=False, 
                                                 bound_forms=bound_forms,
                                                 files=request.FILES,
                                                 )
        
        template_args['action_forms'] = action_forms
        
        # check for form validity
        if bound_forms and self.validate_action_forms(request, action_forms):
            
            for f in action_forms:
                if isinstance(f, ActionModelForm) and self.is_proposal(user_profile, f.instance, **kwargs):
                    return self.create_proposal(request, user_profile, input_data, template_args, **kwargs)
            
            # save if all valids
            for f in action_forms:
                f.full_clean()
                f.save()
            
            # check if pipe is finished
            action_data = kwargs['pipe']
            action_scenario_keys = self.get_action_scenario(action).keys()
            
            # instance data
            final_data = {}
            final_data.update(action_data['data'])
            
            # add pipe data from the models to the data pipe
            for f in action_forms:
                if isinstance(f,ActionModelForm):
                    idata = model_to_dict(f.instance)
                    for k in action_scenario_keys:
                        if k in idata and idata[k]:
                            if not k in final_data:
                                final_data[k] = idata[k]
            
            # check for missing data
            is_finished = True
            for field in action_scenario_keys:
                if not field in final_data:
                    is_finished = False
                    break
            
            # scenario have ended
            if is_finished:
                action_data['completed_date'] = now()
                action_data['data'].update(final_data)
                self.save_actionpipe_data(request, action_data, action_data['akey'], **kwargs)
                return self.manage_action_completed(request, user_profile, template_args, **kwargs)
            
            # otherwise go to the next step
            next_url = self.get_next_url(action_data, **kwargs)
            if next_url == '/'+request.path_info \
                or request.method.lower() == 'get':
                response = self.render(request, template_args, **kwargs)
            else:
                response = HttpResponseRedirect(next_url)
        else:
            response = self.render(request, template_args, **kwargs)
        
        return response

    def manage_action_completed(self, request, user_profile, template_args, **kwargs):
        """
        Handles final pipe action view state
        """
        #return HttpResponseRedirect(kwargs['node'].get_url()+'view/')
        action = kwargs['action']
        template_args['action_is_done'] = True
        template_args['action_forms'] = self.get_validated_forms(self.get_forms_instances(action, 
                                                                 user_profile,
                                                                 kwargs),
                                                                 {},
                                                                 action, 
                                                                 save_forms=False, 
                                                                 bound_forms=False,
                                                                 files=request.FILES,
                                                                 )
        return self.render(request, template_args, **kwargs)


    def finish(self, request, response, **kwargs):
        '''
        Sets final akey cookie
        '''
        # check if the current action pipe is completed for this action
        #if request.method.lower() == 'post':
        akey = self.get_session_user_keys(request)
        user_data = kwargs['pipe']
        user_data = self.save_actionpipe_data(request, user_data, akey, **kwargs)
        response.set_cookie(self.pipe_hash_key, user_data[self.pipe_hash_key])
        return response


    def update_actionpipe_data(self, request, data, akey, **kwargs):
        """
        Update the actionpipe data with provided dict
        Ensures clean and freshness of the pipe_data dict
        """
        
        # get the current refrence action data
        # to avoid race conditions
        # if True == False:
        #data_dict = kwargs.get('pipe')
        data_dict = None
        #data_dict = action_cache.get(self.get_action_cache_key(akey))
        if data_dict is None:
            #if data_dict is None:
            data_dict = self.pipe_table.get_latest(akey, kwargs['action'])
            if data_dict is None:
                data_dict = self.get_default_pipe_data(request, akey, **kwargs)
        
        # decompress contained action data
        if isinstance(data_dict['data'], str) or isinstance(data_dict['data'], unicode):
            data_dict['data'] = json.loads(data_dict['data'])

        # update dict with new values
        for k in data:
            data_dict['data'][k] = data[k]
        
        # clean empty fields
        fields = list(data_dict['data'].keys())
        for field in fields:
            if not data_dict['data'][field]:
                del data_dict['data'][field]
            #remove keys not in pipe
            # clean out of scenario keys
            #elif not field in self.get_action_scenario(kwargs.get('action')).keys():
            #    del data_dict['data'][field]
        
        # ensure json normalize
        data_dict['data'] = json.loads(json.dumps(data_dict['data']))
        
        # markup
        data_dict['action'] = kwargs.get('action')
        
        if not data_dict['path']:
            data_dict['path'] = self.get_referer_path(request)
        
        # ref time ?
        data_dict['ref_time'] = DataPath.get_ref_time()
        return data_dict
    

    def save_actionpipe_data(self, request, data_dict, akey, **kwargs):
        '''
        Saves it to nosql
        This is an "atomic" operation,
        you should not try to save data another way
        because of cache handling
        '''
        # update the data dict with fresh data as a base
        #data_dict = self.update_actionpipe_data(request, data_dict['data'], akey, **kwargs)
        
        # compress
        range_key = data_dict['action']
        
        self.pipe_table.put(akey, range_key, data_dict)
        
        # write to cache
        data_dict['data'] = json.dumps(data_dict['data'], default=API_json_parser)
        action_cache.set(self.get_action_cache_key(akey), data_dict)

        # restore uncompressed
        try:
            data_dict['data'] = json.loads(data_dict['data'])
        except:
            data_dict['data'] = {}

        return data_dict

    def get_next_scenario_node(self, user_data, **kwargs):
        
        action_scenario = self.get_action_scenario(kwargs.get('action'))
        fields = action_scenario.keys()
        
        next_view = None
        next_action = None
        for field in fields:
            if field not in user_data['data']:
                next_view = action_scenario[field].get('class')
                next_action = action_scenario[field].get('action')
                break
        
        return next_view, next_action
    
    def get_next_url(self, user_data, **kwargs):
        '''
        Given pipe action data,
        returns the next view to display
        '''
        next_view, next_action = self.get_next_scenario_node(user_data, **kwargs)

        if next_view is None:
            # return next in list ?
            # if has brother and sisters
            if kwargs['node'].is_leaf_node():
                return kwargs['node'].get_url()+'view/'
            
                if not kwargs['node'].parent:
                    return kwargs['node'].get_url()+'view/'
                
                if kwargs['node'].parent.get_children_count() == 1:
                    return kwargs['node'].get_url()+'view/'
                else:
                    return kwargs['node'].parent.get_url()
            else:
                kwargs['node'].get_url()+'view/'
            
            return user_data['path']+'view/'
            return self.get_reversed_action(self.view_name, 'view', kwargs)
            # if all fields are completed,
            # redirect to last view of the actionpipe
            if user_data['path']:
                return user_data['path']
            else:
                return self.get_reversed_action(self.view_name, 'view', kwargs)

        return self.get_reversed_action(next_view.view_name, next_action, kwargs)

    def get_prev_url(self, user_data, **kwargs):
        # TODO
        raise NotImplemented('Coming next !')
    