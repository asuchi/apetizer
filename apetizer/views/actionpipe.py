'''
Created on 16 mai 2014

@author: rux
'''
from apetizer.storages.kvstore import KVStore
from apetizer.views.httpapi import HttpAPIView
from collections import OrderedDict
import copy
import json
import uuid

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache as action_cache
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.datetime_safe import strftime
from django.utils.timezone import now
from django.forms.models import ModelForm


__all__ = ['ActionPipeView', ]


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
        'akey': 'default',
        # range key
        'user_id': 'guest',
        'pipe_start_time': '',
        'origin_url': '',
        'pipe': 'undefined',
        'pipe_data': json.dumps({}),
    }
    
    class_actions = ['start', 'view', 'prev', 'next', 'end']
    
    pipe_table = KVStore()

    '''
    pipe_scenario defines a sequence of field names
    that has to be filled by the user to complete the pipe action
    these are mapped to view names
    in order to find the needed view to display
    scenario will run until all flaged data elements are filled with something
    '''
    def __init__(self, **kwargs):
        super(ActionPipeView, self).__init__(**kwargs)
        self.pipe_scenario = OrderedDict([('pipe-started',
                                           {'class': self.__class__,
                                            'action': 'start'}
                                           ),
                                          ('pipe-finished',
                                           {'class': self.__class__,
                                            'action': 'finish'}
                                           )])

    def get_session_user_keys(self, request):
        """
        Get actionpipe data container key
        Generates a new one if missing cookie
        """
        akey = request.COOKIES.get('akey', str(uuid.uuid4()))
        if request.user.is_authenticated():
            user_id = str(request.user.id)
        else:
            user_id = 'guest'
        
        # TODO
        # verify session key is correct
        
        return akey, user_id
        
    def get_actionpipe_data(self, request):
        """
        Get the request/session associated current actionpipe data
        Get the action pipe data from cache, dynamodb or default
        This is mainly a shortcut to the pipe util
        """
        akey, user_id = self.get_session_user_keys(request)
        
        # init default data dict
        pipe_data = self.get_default_pipe_data(request, akey, user_id)
        
        # check for data in memcached
        cache_data = action_cache.get(self.get_action_cache_key(akey, user_id))
        if cache_data is None:
            # check for data on dynamodb
            cache_data = self.pipe_table.get_latest(akey, user_id)
            # save to cache
            if cache_data is None:
                action_cache.set(self.get_action_cache_key(akey, user_id),
                                 pipe_data)
                
        if cache_data and 'pipe' in cache_data and cache_data['pipe'] == self.pipe_name:
            pipe_data.update(cache_data)
        
        pipe_data['pipe_activity_time'] = strftime(now(), '%s')
        
        pipe_data['akey'] = akey
        pipe_data['user_id'] = user_id
        
        # decompress contained action data
        if isinstance(pipe_data['pipe_data'], str):
            pipe_data['pipe_data'] = json.loads(pipe_data['pipe_data'])

        # clean empty fields
        fields = list(pipe_data['pipe_data'].keys())
        for field in fields:
            if not pipe_data['pipe_data'][field]:
                del pipe_data['pipe_data'][field]
        
        return pipe_data

    def get_default_pipe_data(self, request, akey, user_id):
        """
        Get a default action data dict
        """
        pipe_data = copy.deepcopy(self.pipe_data_model)

        pipe_data['pipe'] = self.pipe_name

        pipe_data['akey'] = akey
        pipe_data['user_id'] = user_id

        pipe_data['origin_url'] = self.get_referer_path(request)
        pipe_data['pipe_start_time'] = strftime(now(),
                                                '%Y-%m-%d-%H-%M')

        # start new pipe
        pipe_data['pipe_data'] = {}
        return pipe_data


    def get_action_cache_key(self, key, krange):
        """
        Get a correct cache key for action data
        """
        return 'ap-'+str(key)
    
    
    
    def get_next_url(self, user_data, **kwargs):
        '''
        Given pipe action data,
        returns the next view to display
        '''
        # correct user_data to the view default action pipe if missing
        if 'pipe' not in user_data or user_data['pipe'] == 'undefined':
            user_data['pipe'] = self.pipe_name

        fields = self.pipe_scenario.keys()

        next_view = None

        for field in fields:
            if field not in user_data['pipe_data']:
                next_view = self.pipe_scenario[field].get('class')
                next_action = self.pipe_scenario[field].get('action')
                break

        if next_view is None:
            # if all fields are completed,
            # redirect to last view of the actionpipe
            next_view = self.pipe_scenario[field].get('class')
            next_action = self.pipe_scenario[field].get('action')
        
        return self.get_reversed_action(next_view.view_name, next_action, kwargs)
    
    
    def start_action_pipe(self, request):
        '''
        this method manages start of the pipe
        it' meant to be overriden by concerned views
        '''
        # override this method to manage start action custom setup
        return True
    
    def pre_process(self, request, user_profile, input_data, **kwargs):
        """
        Hook before processing the request
        Best place to make user/objects rights management
        """
        # get actual user data
        kwargs['pipe'] = self.get_actionpipe_data(request)
        
        response = self.process(request, user_profile, input_data, **kwargs)
        
        kwargs['pipe'] = self.get_actionpipe_data(request)
        
        return self.finish(request, response, user_data=kwargs['pipe'], **kwargs)
    
    def process_start(self, request, user_profile, input_data, template_args,
                      **kwargs):
        '''
        main processing of the start action
        set's initial values gathered by request get or post
        only fields that exists in the actionpipe configuration are allowed
        '''
        user_data = kwargs.get('pipe')
        
        # check for an existing action
        if user_data['pipe'] != self.pipe_name:
            # set default data
            akey, user_id = self.get_session_user_keys(request)
            user_data = self.get_default_pipe_data(request, akey, user_id)

        # override action with this new one
        user_data['pipe'] = self.pipe_name
        user_data['origin_url'] = self.get_referer_path(request)
        
        # save
        user_data = self.save_actionpipe_data(request, user_data)
        
        # get to the first field url
        first_field = list(self.pipe_scenario.keys())[0]
        
        # to have the corresponding redirection
        redirect_to = reverse(self.pipe_scenario[first_field].get('class').view_name,
                              kwargs={'action': self.pipe_scenario[first_field].get('action')}
                              )

        # add previous parameter for google analytics tracking
        if request.method.lower() == 'get' and request.GET.get('previous'):
            redirect_to += '?previous=' + request.GET.get('previous')

        response = HttpResponseRedirect(redirect_to)
        return response
    
    def process_next(self, request, user_profile, input_data, template_args, **kwargs):
        '''
        call this method to be redirected to the next pipe view
        '''
        return HttpResponseRedirect(self.get_next_url(kwargs.get('pipe'), **kwargs))

    def process_prev(self, request, user_profile, input_data, template_args, **kwargs):
        '''
        call this method to be redirected to the previous pipe view
        '''
        return HttpResponseRedirect(self.get_prev_url(kwargs.get('pipe'), **kwargs))

    def process_reset(self, request, user_profile, input_data, template_args, **kwargs):
        '''
        call this method to be redirected to the previous pipe view
        '''
        return HttpResponseRedirect(self.get_prev_url(kwargs.get('pipe'), **kwargs))
    
    
    def process_end(self, request,
                    user_profile, input_data, template_args, **kwargs):
        '''
        the end view is designed as a callback
        it's is meant to be called only by a get request
        so the logic is not implement in the process method
        but in the get method
        '''
        # test if session exists
        #session_key = request.session.session_key
        #if session_key is None:
            # handle a redirect to the current page 
            # in order to have the session inited
            # this happens when landing
        #    return HttpResponseRedirect(reverse(self.view_name,
        #                                        kwargs={'action': kwargs.get('action',self.default_action)}
        #                                        ))
        
        #
        user_data = kwargs.get('pipe')
        
        
        
        # execute the finish action hook
        response = self.finish_action_pipe(request, **kwargs)
        
        # clean action data if we are finishing the actual pipe
        if user_data['pipe'] == self.pipe_name:
            # markup end action time
            user_data['action_end_time'] = strftime(now(),
                                                    '%Y-%m-%d-%H-%M')

            user_data = self.update_actionpipe_data(request, user_data)
            user_data = self.save_actionpipe_data(request, user_data)

            # removing current akey cookie will rotate the key
            response.delete_cookie('akey')

        return response
    
    def manage_pipe(self, request, user_profile, input_data, template_args, **kwargs):
        
        action = kwargs.get('action', self.default_action)
        action_data = kwargs.get('pipe')
        
        action_forms = self.get_validated_forms(self.get_forms_instances(action),
                                 action_data['pipe_data'],
                                 action,
                                 save_forms=False
                                 )
        
        # check for form validity
        if self.validate_action_forms(request, action_forms):
            self.save_actionpipe_data(request, action_data)
            next_url = self.get_next_url(action_data, **kwargs)
            if next_url == request.path \
                or request.method.lower() == 'GET'.lower():
                
                if settings.DEBUG:
                    debug_data = {}
                    for key in action_data:
                        debug_data[key] = str(action_data[key])
                    template_args['debug_data'] = json.dumps(debug_data)
                    response = self.render(request, template_args, action_data, **kwargs)
                else:
                    response = self.render(request, template_args, {}, **kwargs)
            else:
                response = HttpResponseRedirect(next_url)
        else:
            response = self.render(request, template_args, {}, **kwargs)
        
        return response
    
    def finish_action_pipe(self, request, user_data, **kwargs):
        '''
        this method manages end of the pipe
        it' meant to be overriden by concerned views
        '''
        # figure out if next_url is current
        next_url = self.get_next_url(user_data, **kwargs)
        if next_url != request.path:
            return HttpResponseRedirect(next_url)
        
        # do the final stuff ...
        
        # override this method to manage correct end setup per end action view
        response = HttpResponseRedirect(user_data['origin_url'])
        return response

    def finish(self, request,
               response, user_data=None, override=False, **kwargs):
        '''
        Tests if the action required data have been all gathered
        If not, it manages redirect to the correct view
        Else, it redirects to the corresponding action end
        '''
        if user_data == None:
            user_data = kwargs.get('pipe')
        
        # set cooky for pipeline tracking
        # we need to have an extra cookie
        # in order to maintain data across different auhtentication
        if 'akey' in user_data:
            response.set_cookie('akey', user_data['akey'])

        if request.method == 'GET':
            return response

        # when it's a new user
        # accessing directly the view without an action started
        # we set the default action to the view name
        if user_data['pipe'] == 'undefined':
            #user_data['pipe'] = self.pipe_name
            #if not 'pipe_data' in user_data:
            #    user_data['pipe_data'] = {}
            self.update_actionpipe_data(request, user_data['pipe_data'])

        if override:
            next_url = self.get_next_url(user_data, **kwargs)
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
                #f.full_clean()
                is_valid_form = f.is_valid()
                if not is_valid_form:
                    #all_forms_valid = False
                    if len(f.errors) or len(f.non_field_errors()):
                        # check error field are not in hidden/ignored fields
                        # and gether their errors as request messages
                        for field in f.errors:
                            all_forms_valid = False
                            error_message = u'<b>%s</b> %s' % (f[field].label, f.errors[field])
                            messages.error(request, error_message)

                        for message in f.non_field_errors():
                            messages.error(request, message)
                            all_forms_valid = False
                    else:
                        for field in f.fields:
                            try:
                                f.fields[field].run_validators(f[field].value())
                            except ValidationError as e:
                                error_message = u'<b>%s</b> %s' % (f[field].label, e.messages )
                                messages.error(request, error_message)
                                all_forms_valid = False
                                f.errors[field] = e.messages[0]
        
        return all_forms_valid


    def update_actionpipe_data(self, request, data, akey=None, user_id=None):
        """
        Update the actionpipe data with provided dict
        Ensures clean and freshness of the pipe_data dict
        """
        if akey is None or user_id is None:
            akey, user_id = self.get_session_user_keys(request)

        # get the current refrence action data
        # to avoid race conditions
        data_dict = action_cache.get(self.get_action_cache_key(akey, user_id))
        if data_dict is None:
            data_dict = self.pipe_table.get_latest(akey, user_id)
            if data_dict is None:
                data_dict = self.get_default_pipe_data(request, akey, user_id)
        
        # decompress contained action data
        if isinstance(data_dict['pipe_data'], str):
            data_dict['pipe_data'] = json.loads(data_dict['pipe_data'])
        
        # update dict with new values
        for k in data:
            data_dict['pipe_data'][k] = data[k]
        
        # clean empty fields
        fields = list(data_dict['pipe_data'].keys())
        for field in fields:
            if not data_dict['pipe_data'][field]:
                del data_dict['pipe_data'][field]

        # ensure json normalize
        data_dict['pipe_data'] = json.loads(json.dumps(data_dict['pipe_data']))

        return data_dict

    def save_actionpipe_data(self, request, data_dict, akey=None,
                             user_id=None):
        '''
        Saves it to nosql
        This is an "atomic" operation,
        you should not try to save data another way
        because of cache handling
        '''
        if akey is None or user_id is None:
            akey, user_id = self.get_session_user_keys(request)

        # update the data dict with fresh data as a base
        data_dict = self.update_actionpipe_data(request, data_dict['pipe_data'], akey=akey,
                                                user_id=user_id)

        # compress
        data_dict['pipe_data'] = json.dumps(data_dict['pipe_data'])

        # write
        action_cache.set(self.get_action_cache_key(akey, user_id), data_dict)
        self.pipe_table.put(akey, user_id, data_dict)

        # restore uncompressed
        try:
            data_dict['pipe_data'] = json.loads(data_dict['pipe_data'])
        except:
            data_dict['pipe_data'] = {}

        return data_dict
