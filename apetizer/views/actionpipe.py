'''
Created on 16 mai 2014

@author: rux
'''
from collections import OrderedDict
import copy
import json
import uuid

from django.contrib import messages
from django.core.cache import cache as action_cache
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.datetime_safe import strftime
from django.utils.timezone import now

from apetizer.storages.kvstore import KVStore
from apetizer.views.httpapi import HttpAPIView


__all__ = ['ActionPipeView',]



class ActionPipeView(HttpAPIView):
    '''
    base class for an action pipe view 
    '''
    pipe_name = 'undefined'
    
    pipe_table = KVStore()
    
    """
    Default action data dict
    """
    pipe_data_model = {
        
        # hash_key
        'akey':'default',
        # range key
        'user_id':'guest',
        
        'pipe_start_time':'',
        'origin_url':'',
        'pipe':'undefined',
        'pipe_data':json.dumps({}),
    
    }
    internal_actions = ['start', 'view', 'prev', 'next', 'end', 'doc']
    
    pipe_table = KVStore()
    '''
    pipe_scenario defines a sequence of field names 
    that has to be filled by the user to complete the pipe action
    
    these are mapped to view names 
    in order to find the needed view to display
    
    scenario will run until all flaged data elements are filled with something
    '''
    def __init__(self, **kwargs):
        HttpAPIView.__init__(self, **kwargs)
        self.pipe_scenario = OrderedDict([
                # exemple start of pipe
                ('pipe-started', {'class':self.__class__, 'action':'start'}),
                # exemple view of pipe
                ('pipe-viewed', {'class':self.__class__, 'action':'view'}),
                # exemple end of pipe
                ('pipe-finished', {'class':self.__class__, 'action':'finish'})
                ])
        
        
    def get_default_pipe_data(self, akey, user_id):
        """
        Get a default action data dict
        """
        pipe_data = copy.deepcopy(self.pipe_data_model)
        
        pipe_data['akey'] = akey
        pipe_data['user_id'] = user_id
        
        pipe_data['pipe_start_time'] = strftime(now(),'%Y-%m-%d-%H-%M')
        
        pipe_data['pipe_data'] = {}
        
        return pipe_data
    
    def get_session_user_keys(self, request):
        """
        Get actionpipe data container key
        Generates a new one if missing cookie
        """
        akey = request.COOKIES.get('akey', None)
        
        if akey == None:
            akey = str(uuid.uuid4())
        
        if request.user.is_authenticated():
            user_id = str(request.user.id)
        else:
            user_id = 'guest'
        
        return akey, user_id
    
    
    def get_actionpipe_data(self, request):
        """
        Get the request/session associated current actionpipe data
        Get the action pipe data from cache, dynamodb or default
        This is mainly a shortcut to the pipe util
        """
        akey, user_id = self.get_session_user_keys(request)
        
        # init default data dict
        pipe_data = self.get_default_pipe_data(akey, user_id)
        
        # check for data in memcached
        cache_data = action_cache.get( self.get_action_cache_key( akey, user_id ) )
        
        if cache_data == None:
            # check for data on dynamodb
            cache_data = self.pipe_table.get_latest( akey )
            
            # save to cache
            if cache_data == None:
                action_cache.set( self.get_action_cache_key( akey, user_id ), pipe_data )
        
        if cache_data:
            pipe_data.update(cache_data)
        
        pipe_data['akey'] = akey
        pipe_data['user_id'] = user_id
        
        # decompress contained action data
        if type(pipe_data['pipe_data']) == type('') or type(pipe_data['pipe_data']) == type(u''):
            pipe_data['pipe_data'] = json.loads(pipe_data['pipe_data'])
        
        # clean empty fields
        fields = list(pipe_data['pipe_data'].keys())
        for field in fields:
            if not pipe_data['pipe_data'][field]:
                del pipe_data['pipe_data'][field]
        
        return pipe_data
    
    
    def get_action_cache_key(self, key, krange):
        """
        Get a correct cache key for action data
        """
        return 'ap-'+str(key)
    
    
    
    def get_next_url(self, user_data):
        '''
        Given pipe action data, 
        returns the next view to display
        '''
        # correct user_data to the view default action pipe if missing
        if not 'pipe' in user_data:
            user_data['pipe'] = self.pipe_name
        
        fields = self.pipe_scenario.keys()
        
        next_view = None
        
        for field in fields:
            if not field in user_data['pipe_data']:
                
                next_view = self.pipe_scenario[field].get('class')
                next_action = self.pipe_scenario[field].get('action')
                break
        
        if next_view is None:
            # if all fields are completed, redirect to last view of the actionpipe
            next_view = self.pipe_scenario[field].get('class')
            next_action = self.pipe_scenario[field].get('action')
        
        return reverse( next_view.view_name, kwargs={'action':next_action})
    
    
    def start_action_pipe(self, request):
        '''
        this method manages start of the pipe
        it' meant to be overriden by concerned views
        '''
        # override this method to manage start action custom setup
        return True
    
    def process_start(self, request, user_profile, input_data, template_args, **kwargs):
        '''
        main processing of the start action
        set's initial values gathered by request get or post
        only fields that exists in the actionpipe configuration are allowed
        '''
        
        # test if session exists
        akey, user_id = self.get_session_user_keys(request)
        
        # get actual user data
        user_data = self.get_actionpipe_data(request)
        
        # check for an existing action
        if user_data['pipe'] != self.pipe_name:
            # set default data
            user_data = self.get_default_pipe_data(akey, user_id)
        
        # override action with this new one
        user_data['pipe'] = self.pipe_name
        user_data['origin_url'] = self.get_referer_path(request)
        
        # filter get/post params
        request_data = {}
        if request.method.lower() == 'get':
            request_data = self.update_data_with_get(request, user_data['pipe_data'])
        elif request.method.lower() == 'post':
            request_data = self.update_data_with_post(request, user_data['pipe_data'])
        
        # update actionpipe data
        for k in request_data:
            if k in self.pipe_scenario.keys():
                user_data['pipe_data'][k] = request_data[k]
        
        # save
        user_data = self.save_actionpipe_data(request, user_data)
        
        # get to the first field url
        first_field = list(self.pipe_scenario.keys())[0]
        
        # to have the corresponding redirection
        redirect_to = reverse( self.pipe_scenario[first_field].get('class').view_name, kwargs={'action':self.pipe_scenario[first_field].get('action')} )

        # add previous parameter for google analytics tracking
        if request.method.lower() == 'get' and request.GET.get('previous'):
            redirect_to += '?previous=' + request.GET.get('previous')
        
        response = HttpResponseRedirect(redirect_to)
        
        # flush the request
        return self.finish(request, response, user_data)
        
    def process_view(self, request, user_profile, input_data, template_args, **kwargs):
        '''
        override this method to use same request processing for GET and POST
        '''
        user_data = self.get_actionpipe_data(request)
        
        return self.render(request, template_args, user_data, **kwargs)
    
    def process_next(self, request, user_profile, input_data, template_args, **kwargs):
        '''
        call this method to be redirected to the next pipe view
        '''
        return HttpResponseRedirect(self.get_next_url(self.get_actionpipe_data(request), **kwargs))
    
    def process_prev(self, request, user_profile, input_data, template_args, **kwargs):
        '''
        call this method to be redirected to the previous pipe view
        '''
        return HttpResponseRedirect(self.get_prev_url(self.get_actionpipe_data(request), **kwargs))
    
    def process_reset(self, request, user_profile, input_data, template_args, **kwargs):
        '''
        call this method to be redirected to the previous pipe view
        '''
        return HttpResponseRedirect(self.get_prev_url(self.get_actionpipe_data(request), **kwargs))
    
    def process_graph(self, request, user_profile, input_data, template_args, **kwargs):
    
        user_data = self.get_actionpipe_data(request)
        
        return self.render(request, template_args, user_data, **kwargs)
    
    
    def process_end(self, request, user_profile, input_data, template_args, **kwargs):
        '''
        the end view is designed as a callback
        it's is meant to be called only by a get request
        so the logic is not implement in the process method
        but in the get method
        '''
        # test if session exists
        session_key = request.session.session_key
        if session_key == None:
            # handle a redirect to the current page in order to have the session inited
            return HttpResponseRedirect( reverse(self.view_name, kwargs={'action':kwargs.get('action',self.default_action)}) )
        
        #
        user_data = self.get_actionpipe_data(request)
        
        # execute the finish action hook
        response = self.finish_action_pipe(request)
        
        # clean action data if we are finishing the actual pipe
        if user_data['pipe'] == self.pipe_name:
            
            # markup end action time
            user_data['action_end_time'] = strftime(now(),'%Y-%m-%d-%H-%M')
            
            user_data = self.update_actionpipe_data(request, user_data)
            user_data = self.save_actionpipe_data(request, user_data)
            
            # removing current akey cookie will rotate the key
            response.delete_cookie('akey')
            
        return response

    
    def finish_action_pipe(self, request, user_data):
        '''
        this method manages end of the pipe
        it' meant to be overriden by concerned views
        '''
        # override this method to manage correct end setup per end action view
        response = HttpResponseRedirect( user_data['origin_url'] )
        return response

    
    def finish(self, request, response, user_data=None, override=False, **kwargs):
        '''
        Tests if the action required data have been all gathered
        If not, it manages redirect to the correct view
        Else, it redirects to the corresponding action end
        '''
        
        # set cooky for pipeline tracking
        # we need to have an extra cookie 
        # in order to maintain data across different auhtentication
        if 'akey' in user_data:
            response.set_cookie('akey', user_data['akey'] )
        
        if request.method == 'GET':
            return response
        
        # when it's a new user accessing directly the view without an action started
        # we set the default action to the view name
        if user_data['pipe'] == 'undefined':
            user_data['pipe'] = self.pipe_name
            self.update_actionpipe_data(request, user_data)
        
        if override:
            
            next_url = self.get_next_url(user_data)
            if next_url != request.path:
                return response
            else:
                return HttpResponseRedirect(next_url)
            
        return response

    
    def validate_action_forms(self, request, forms):
        '''
        Validate a given list of forms 
        and adds validation error message to request
        '''
        all_forms_valid = True
        if request.method == 'POST':
            for f in forms:
                if not f.is_valid():
                    if len(f.errors) or len(f.non_field_errors()):
                        # check error field are not in hidden/ignored fields
                        # and gether their errors as request messages
                        for field in f.errors:
                            if not field in f.hidden_fields:
                                all_forms_valid = False
                                error_message = u'<b>%s</b> %s' % ( f[field].label, f.errors[field])
                                messages.error(request, error_message)
                        
                        for message in f.non_field_errors():
                            messages.error(request, message)
                            all_forms_valid = False
                    
        return all_forms_valid
    
    
    
    
    def filter_data_with_forms(self, data, forms):
        '''
        filters a dict by values names as 
        the fields in the form classes provided
        also check for oversized values
        '''
        data_dict = {}
        
        form_keys = []
        
        for form_class in forms:
            form = form_class()
            for field_name in form.fields:
                if not field_name in form_keys:
                    form_keys.append(field_name)
        
        for k in data.keys():
            # check if key in form_keys
            if k in form_keys:
                data_dict[k] = data[k]
        
        return data_dict
    
    
    

    
    def update_data_with_post(self, request, data, forms=None):
        """
        Update data dict with request post value
        and filter by form if provided
        """
        # prepare incomming data
        if forms is None:
            clean_data = request.POST
        else:
            clean_data = self.filter_data_with_forms( request.POST, forms )
        
        # update the dict
        for k in clean_data.keys():
            # check for oversized post value
            if not k in ('login_password','csrfmiddlewaretoken') \
                and len( clean_data[k] ) < 4096:
                
                data[k] = clean_data[k]
        
        return data
    
    
    def update_data_with_get(self, request, data, forms=None):
        """
        Update data dict with request get value
        and filter by form if provided
        """
        # prepare incomming data
        if forms is None:
            clean_data = request.GET
        else:
            clean_data = self.filter_data_with_forms( request.GET, forms )
        
        # update the dict
        for k in clean_data.keys():
            # check for oversized post value
            if not k in ('login_password','csrfmiddlewaretoken') \
                and len( clean_data[k] ) < 4096:
                
                data[k] = clean_data[k]
        
        return data
    
    
    
    def update_actionpipe_data(self, request, pipe_data, akey=None, user_id=None):
        """
        Update the actionpipe data with provided dict
        Ensures clean and freshness of the pipe_data dict
        """
        if akey is None or user_id is None:
            akey, user_id = self.get_session_user_keys(request)
        
        # get the current refrence action data
        # to avoid race conditions
        data_dict = action_cache.get( self.get_action_cache_key( akey, user_id ) )
        if data_dict == None:
            data_dict = self.pipe_table.get_latest( akey )
            if data_dict == None:
                data_dict = self.get_default_pipe_data(akey, user_id)
        
        # update dict with new values
        for k in pipe_data:
            data_dict[k] = pipe_data[k]
        
        # clean empty fields
        fields = list(pipe_data['pipe_data'].keys())
        for field in fields:
            if not pipe_data['pipe_data'][field]:
                del pipe_data['pipe_data'][field]
        
        # ensure json normalize
        pipe_data['pipe_data'] = json.loads(json.dumps(data_dict['pipe_data']))
        
        return data_dict
        
        
    def save_actionpipe_data(self, request, data_dict, akey=None, user_id=None):
        '''
        Saves it to nosql
        This is an "atomic" operation, 
        you should not try to save data another way 
        because of cache handling
        '''
        if akey is None or user_id is None:
            akey, user_id = self.get_session_user_keys(request)
        
        # update the data dict with fresh data as a base
        data_dict = self.update_actionpipe_data(request, data_dict, akey=akey, user_id=user_id)
        
        # compress
        data_dict['pipe_data'] = json.dumps(data_dict['pipe_data'])
        
        # write
        action_cache.set( self.get_action_cache_key( akey, user_id ), data_dict )
        self.pipe_table.put(akey, user_id, data_dict )
        
        # restore uncompressed
        try:
            data_dict['pipe_data'] = json.loads(data_dict['pipe_data'])
        except:
            data_dict['pipe_data'] = {}
        
        return data_dict
    
    
    