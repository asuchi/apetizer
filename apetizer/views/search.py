'''
Created on 24 oct. 2013

@author: rux
'''
import datetime
import json
import logging
import math
import operator
from time import time
import traceback
import unicodedata

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import EmptyPage, Paginator, Page
from django.core.urlresolvers import reverse
from django.db.models.query_utils import Q
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template.context import RequestContext
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext as _, ugettext
from geopy import units
import geopy.distance

from apetizer import _search_key_points
from apetizer.directory import _search_key_sort_results, \
    _search_key_page_results
from apetizer.directory.dates import start_datetimetz_from_string, end_datetimetz_from_string
from apetizer.directory.i10n import round_to, pretty_distance
from apetizer.directory.items import _search_drilldown_cache
from apetizer.directory.utils import update_search_session_vars, \
    get_search_session_vars, SEARCH_KEY_NAME, get_search_key, \
    clean_cache_search_key, assign_cache_search_render, \
    get_cache_search_render, save_search_session_vars, SEARCH_KEY_COOKIE_NAME
from apetizer.forms.search import SearchTypesForm, \
    SearchSettingsForm, SearchAgeForm, SearchSortForm, SearchPageForm, SearchInputForm, \
    UserInputForm, SearchKeywordForm
from apetizer.models import Item
from apetizer.templatetags.drilldown_tags import drilldown_item_title
from apetizer.templatetags.search_tags import get_applied_form_filters
from apetizer.views.visitor import VisitorView


logger = logging.getLogger(__name__)


'''
How many map results will we show (max)?
'''
MAX_MAP_RESULTS = getattr(settings, 'MAX_MAP_RESULTS', 500)

CACHE_SEARCH_KEY_DURATION = getattr(settings, 'CACHE_SEARCH_KEY_DURATION', 3600)
CACHE_SEARCH_KEY_SORT = getattr(settings, 'CACHE_SEARCH_KEY_SORT', False)
CACHE_SEARCH_KEY_PAGE = getattr(settings, 'CACHE_SEARCH_KEY_PAGE', False)

'''
How many results will we wade through for sorting?
'''
MAX_SORT_RESULTS = MAX_MAP_RESULTS

RESULTS_PER_PAGE = 20


'''
Default distance from center for searches
'''
DEFAULT_DISTANCE = 600

'''
Default distance from center for searches at higher levels

These are purposely chosen to mesh with the size of our search map and google's 
zoom levels. 
'''
DEFAULT_DISTANCE_CITY = 4600
DEFAULT_DISTANCE_COUNTRY = 640000

'''
How many results must we have before we stop zooming out?
'''
DEFAULT_RESULTS_UNTIL_NO_ZOOM = 5
RESULTS_UNTIL_NO_ZOOM_CITY = 5

'''
How much search area (radius in meters) before we stop zooming out?
'''
DEFAULT_DISTANCE_UNTIL_NO_ZOOM = 6000
DEFAULT_DISTANCE_UNTIL_NO_ZOOM_CITY = DEFAULT_DISTANCE_CITY * 2 # Zoom once
DEFAULT_DISTANCE_UNTIL_NO_ZOOM_COUNTRY = DEFAULT_DISTANCE_COUNTRY # Don't zoom

'''
How results can be sorted
'''
SORT_OPTIONS = ('cheapest', 'most_expensive', 'closest', 'newest')

'''
These helper functions implement intelligence around the zooming / result count
parameters above.
'''

class SearchView(VisitorView):
    
    view_template = 'search/main.html'
    view_name = 'search'
    
    class_actions = ['search']
    class_action_templates = {'search':'search/main.html'}
    
    default_action = 'search'
    
    def process_search(self, request, user_profile, input_data, template_args, path=None, **kwargs):
        """
        process default incoming request
        """
        if not _search_drilldown_cache.has_key(path):
            path = 'localhost'
        path = None
        if request.method.lower() == 'get':
            return self.search_get(request, user_profile, input_data, template_args, path=path, **kwargs)
        elif request.method.lower() == 'post':
            return self.search_post(request, user_profile, input_data, template_args, path=path, **kwargs)
        else:
            return super(SearchView, self).process_search(request, user_profile, input_data, template_args, **kwargs)
    
    
    def search_get(self, request, user_profile, input_data, template_args, path=None, **kwargs):
        """
        process initial html request
        """
        # remove page from path and get page_number
        paginator_path_page_number = 1
        if path:
            try:
                paginator_path_page_number = int(path[-1:])
                if path[-6:-2] == 'page':
                    path = path[:-7]
            except:
                paginator_path_page_number = 1
        #if path and path[0] != '/':
        #    path = '/'+path
        
        # first of all, check if path is provided if it exists in drilldown
        # otherwise, raise 404
        try:
            if path != None and not _search_drilldown_cache.has_key(path):
                raise Http404
        except:
            raise Http404
        
        # test skey reset - search key is in the url but empty
        if request.GET.get('skey',None) == '' and path == None:
            path = '/localhost'
        
        #elif request.GET.get('skey', None) != None and path != None:
            # path and search key are conflicting
            # redirect to search key
        #    response = HttpResponseRedirect(request.path+'?skey='+request.GET.get('skey'))
        #    return response
        
        #user_data['search_path'] = currentNode
        
        # test if we have a search key, witch tells you are a user
        search_key = get_search_key(request)
        if search_key != None and (path == None or path == '/localhost/'):
            #
            user_data = get_search_session_vars(request)
            
            # update key data with provided path
            if path == None:
                user_data['search_tab'] = 'list'
            else:
                user_data['search_tab'] = 'tree'
                user_data = self.update_search_data(path, user_data)
            
            #if path != None or 'page' in request.GET or ( len(request.GET) > 0 and request.GET.get('skey',None) == None ):
            user_data, search_key = update_search_session_vars(request, user_data)
            #else:
            #    search_key = get_search_key(request)
            
            # redirect to the vehicle with the skey in the url
            # if no path and search key is provided, redirect to the path with the key in the url
            if path == None and search_key != None and request.GET.get('skey',None) == None:
                response = HttpResponseRedirect(request.path+'?skey='+search_key)
            else:
                render_data = get_cache_search_render( search_key )
                if render_data != None:
                    template_vars = render_data
                    if settings.DEBUG:
                        logger.info('------------> Sending cached search render data '+search_key)
                else:
                    search_session = self.get_session(request, kwargs)
                    search_session.update(request, path, search_key, user_data, template_args, kwargs)
                    template_vars = search_session.get_render_data()
                    
                template_vars['sort_form'] = SearchSortForm(initial=user_data)
                template_vars['page_form'] = SearchPageForm(initial=user_data)
                
                template_vars['tab'] = user_data['search_tab']
                
                template_vars.update(template_args)
                
                response = self.render(request, template_vars, **kwargs)
            
            return response
            return self.finish(request, response)
            
        else:
            
            # we simply display the drilldown content 
            # as it's supposed to be user without "search session"
            # we provide the view the raw list of vehicles from the drilldown
            
            #user_data = {'search_display_unvisible':'on'}
            user_data = get_search_session_vars(request)
            
            user_data['search_display_unvisible'] = 'on'
            user_data['search_tab'] = 'tree'
            
            user_data = self.update_search_data(path, user_data)
            
            user_data['page'] = paginator_path_page_number
            
            user_data, search_key = update_search_session_vars(request, user_data)
            
            search_session = self.get_session(request, kwargs)
            search_session.update(request, path, search_key, user_data, template_args, kwargs)
            
            template_vars = search_session.get_render_data()
            
            template_vars['sort_form'] = SearchSortForm(initial=user_data)
            template_vars['page_form'] = SearchPageForm(initial=user_data)
            
            template_vars['tab'] = 'tree'
            
            template_vars.update(template_args)
                
            response = self.render(request, template_vars, **kwargs)
            
            return response
            return self.finish(request, response)
            
        
        
    def update_search_data(self, path, user_data ):
        '''
        update user_data from search_key 
        with the drilldown url data
        '''
        
        if path and _search_drilldown_cache.data_map.has_key(path):
            
            _data = _search_drilldown_cache.get_key_data(path)
            
            #
            key_type = None
            if 'admin3' in _data and len(_data['admin3']) == 1:
                key_type = 'admin3'
            elif 'admin2' in _data and len(_data['admin2']) == 1:
                key_type = 'admin2'
            elif 'region' in _data and len(_data['region']) == 1:
                key_type = 'region'
            elif 'admin0' in _data and len(_data['admin0']) == 1:
                key_type = 'admin0'
            else:
                if 'data' in _data:
                    for key in _data['data']:
                        if _data['data'][key] == path:
                            key_type = key
                
            
            if key_type:
                
                obj_type_slug_data = _search_drilldown_cache.get_object(key_type, _data[key_type].keys()[0])
                
                user_data['search_input'] = obj_type_slug_data['data']['label']
                user_data['search_lat'] = obj_type_slug_data['stats']['lat']
                user_data['search_lng'] = obj_type_slug_data['stats']['lng']
                user_data['search_radius'] = obj_type_slug_data['stats']['radius']
                
                if key_type == 'admin3':
                    user_data['search_admin3'] = obj_type_slug_data['data']['label']
                else:
                    if 'search_admin3' in user_data:
                        del user_data['search_admin3']
                    
                if key_type == 'region':
                    user_data['search_l1'] = obj_type_slug_data['data']['label']
                else:
                    if 'search_l1' in user_data:
                        del user_data['search_l1']
                
                if key_type == 'admin2':
                    user_data['search_l2'] = obj_type_slug_data['data']['label']
                else:
                    if 'search_l2' in user_data:
                        del user_data['search_l2']
                
            else:
                pass
            
            # manage brand
            make_type = None
            if 'admin3-make' in _data and len(_data['admin3-make']) == 1:
                make_type = 'admin3-make'
            elif 'admin2-make' in _data and len(_data['admin2-make']) == 1:
                make_type = 'admin2-make'
            elif 'make' in _data and len(_data['make']) == 1:
                make_type = 'make'
            else:
                if 'data' in _data:
                    if 'make' in _data['data']:
                        make_type = 'make'
            
            if make_type:
                # get the make name
                if 'data' in _data and 'make' in _data['data']:
                    make_key = _data['data'][make_type]
                else:
                    make_key = _data[make_type].keys()[0]
                
                if len(make_type.split('-')) > 1:
                    make_slug = make_key.split('/')[1]
                else:
                    make_slug = make_key
                
                make_label = _search_drilldown_cache.get_object('make', make_slug)['data']['label']
                
                #make = Make.objects.get(brand=make_label)
                #user_data['brand'] = make.id
            else:
                # remove brand filter
                if path:
                    if 'brand' in user_data:
                        del user_data['brand']
            
            # manage type
            key_type = None
            if 'admin3-type' in _data and len(_data['admin3-type']) == 1:
                key_type = 'admin3-type'
            elif 'admin2-type' in _data and len(_data['admin2-type']) == 1:
                key_type = 'admin2-type'
            elif 'type' in _data and len(_data['type']) == 1:
                key_type = 'type'
            else:
                if 'data' in _data:
                    if 'type' in _data['data']:
                        key_type = 'type'
                
            if key_type:
                
                if 'data' in _data and 'make' in _data['data']:
                    key_type = _data['data'][key_type]
                else:
                    type_key = _data[key_type].keys()[0]
                
                if len(key_type.split('-')) > 1:
                    type_slug = type_key.split('/')[1]
                else:
                    type_slug = type_key
                
                type_label = _search_drilldown_cache.get_object('type', type_slug)['data']['label']
                
                # WARNING SHOULD BE USED
                # vehicle_type = VehicleType.objects.get(name_fr=type_label)
                
                # remove all possibly selected vehicle types
                user_data_keys = user_data.keys()
                for key in user_data_keys:
                    if key.split('_')[0] == 'type':
                        del user_data[key]
                
                # add the key
                # user_data['type_'+vehicle_type.slug] = True
            else:
                user_data_keys = user_data.keys()
                for key in user_data_keys:
                    if key.split('_')[0] == 'type':
                        del user_data[key]
        
        user_data['search_path'] = path
        
        return user_data
        


    def search_post(self, request, user_profile, input_data, template_args, path=None, **kwargs):
        """
        process a request including settings
        """
        # remove page from path and get page_number
        try:
            paginator_path_page_number = int(path[-1:])
            if path[-6:-2] == 'page':
                path = path[:-7]
        except:
            paginator_path_page_number = 1
        
        # first of all, check if path is provided if it exists in drilldown
        # otherwise, raise 404
        if path != None and not _search_drilldown_cache.data_map.has_key(path):
            raise Http404
        
        if path != None:
            user_data = get_search_session_vars(request)
        else:
            user_data = {}
        
        # 
        user_data['search_tab'] = 'list'
        
        if path == None:
            user_data, search_key = update_search_session_vars(request, user_data)
        else:
            user_data = self.update_search_data(path, user_data)

            
            # special override for pagination using a GET value
            if request.GET.get('page',None) == None and request.POST.get('page',None) == None:
                user_data['page'] = 1
            
            if request.POST.get('page',None) != None:
                user_data['page'] = request.POST.get('page')
            if request.GET.get('page',None) != None:
                user_data['page'] = request.GET.get('page')
            
            if paginator_path_page_number != user_data['page']:
                user_data['page'] = paginator_path_page_number
            
            user_data, search_key = save_search_session_vars(request, user_data)
        
        # check for cached render
        render_data = get_cache_search_render( search_key )
        if render_data != None:
            template_vars = render_data
            if settings.DEBUG:
                logger.info('------------> Sending cached search render data')
        else:
            # render data
            search_session = self.get_session(request, kwargs)
            search_session.update(request, path, search_key, user_data, template_args, kwargs)
            template_vars = search_session.get_render_data()
        
        # ajax version
        if 'results_only' in request.POST:
            
            response_content = u'<div>'
            
            # page title
            response_content += '<div id="title" >'+template_vars['page_title_snippet']+' - Buzzcar'+'</div>'
            
            # search input
            response_content += '<div id="input" >'+template_vars['search_banner_snippet']+'</div>'
            
            # header
            response_content += '<div id="header" >'+template_vars['page_header_snippet']+'</div>'
            
            # content
            response_content += '<div id="content" >'+template_vars['page_content_snippet']+'</div>'
            
            # filters
            response_content += '<div id="applied" >'+template_vars['filters_applied_snippet']+'</div>'
            
            # vehicles
            response_content += '<div id="results" >'+template_vars['car_selection_snippet']+'</div>'
            
            # drilldown
            response_content += '<div id="drilldown" >'+template_vars['drilldown_selection_snippet']+'</div>'
            
            # messages
            response_content += '<div id="messages" >'+self.render_messages(request)+'</div>'
            
            response_content += '</div>'
            
            response = HttpResponse(response_content)
        else:
            # redirect to full page version
            response = HttpResponseRedirect(request.path+'?'+SEARCH_KEY_NAME+'='+search_key)
            
        return response
        
    def get_session(self, request, kwargs):
        search_session = SearchSession(request, kwargs)
        return search_session
    
    def render_messages(self, request):
        return render_to_string('includes/messages.html', context_instance=RequestContext(request))
    
    
    def finish(self, request, response, **kwargs):
        # set the skey coocky    
        search_key = get_search_key(request)
        if search_key is not None:
            response.set_cookie(SEARCH_KEY_COOKIE_NAME, search_key)

        response = super(SearchView, self).finish(request, response, **kwargs)

        return response
    
# maximum search radius in meters, 80km here
MAX_SEARCH_RADIUS = 85000# 85km
MIN_SEARCH_RADIUS = 500


class SearchSession():
    
    search_key = session_key = path_key = address = path = None
    skip_search = False
    
    max_results = 500

    filters = template_vars = user_data = json_data = {}
    content = u''
    json_data_string = ''
    
    def __init__(self, request, kwargs):
        
        self.kwargs= kwargs
        self.request = request
        self.user_data = get_search_session_vars(request)
        self.search_key = get_search_key(request)
        self.session_key = request.session.session_key
        
    def update(self, request, path, search_key, user_data, template_args, kwargs):
        
        self.kwargs = kwargs
        self.path = path
        self.path_key = path
        
        self.request = request
        
        self.user_data = user_data
        self.search_key = search_key
        
        self.search(template_args, kwargs)
        
    def search(self, template_args, kwargs):
        '''
        Main reservation search page
        '''
        if settings.DEBUG:
            bench_start = time()
        self.kwargs= kwargs
        self.skip_search = False
        
        self.filters = {}
        self.template_vars = template_args
        
        self.get_location()
        self.get_dates()
        self.get_filters()
        
        self.search_results = False
        
        # get the drilldown data
        if self.path_key and _search_drilldown_cache.data_map.has_key(self.path_key):
            self.data = _search_drilldown_cache.get_key_data( self.path_key )
        else:
            if self.search_distance < 10000 and 'search_admin3' in self.user_data:
                self.path_key = slugify(self.user_data['search_admin3'])
            
            if self.search_distance > 20000 or not self.path_key or not _search_drilldown_cache.data_map.has_key(self.path_key):
                
                if 'search_l2' in self.user_data:
                    self.path_key = slugify(self.user_data['search_l2'])
                
                if self.search_distance > 45000 or not _search_drilldown_cache.data_map.has_key(self.path_key):
                    
                    if 'search_l1' in self.user_data:
                        
                        self.path_key = slugify(self.user_data['search_l1'])
                        
                        if not _search_drilldown_cache.data_map.has_key(self.path_key):
                            self.path_key = 'localhost'
                    else:
                        self.path_key = 'localhost'
            
            # get the corresponding drilldown data
            if _search_drilldown_cache.has_key(self.path_key):
                self.data = _search_drilldown_cache.get_key_data(self.path_key)
            else:
                self.data = {}
        
        self.warn_no_results = False
        
        # if no path in the url, we are on a raw search by lat/lng/radius
        if self.path is None:
            
            search_kwargs = build_extra_search_kwargs(self.start_time_tz, 
                                                      self.end_time_tz, 
                                                      1,
                                                      self.filters)
            if self.show_all_nodes:
                search_kwargs['show_all_nodes'] = self.show_all_nodes
                
            self.search_results = self.paginated_sorted_search(self.request, 
                                                               self.address, 
                                                               search_key=self.search_key, 
                                                               distance=self.search_distance, 
                                                               **search_kwargs)
                        
            if self.search_results and self.search_results.count == 0:
                self.warn_no_results = True
        
        # if we have a path or no results from the raw search
        if self.path is not None or not self.search_results or self.search_results.count == 0:
            self.request.distance = self.search_distance
            if 'item' in self.data and len(self.data['item'].keys()):
                search_results = Item.objects.filter(id__in=self.data['item'].keys(),
                                                               visible=True)
                search_results.search_options = {
                    'location': self.address,
                    'request': self.request,
                    'start_time': self.start_time,
                    'end_time': self.end_time,
                    'search_key': self.search_key,
                    'show_all_nodes': self.show_all_nodes
                }

                # robot version
                if self.user_data['search_tab'] == 'tree':
                    self.search_results = SearchPaginator(search_results, 150)
                else:
                    self.search_results = SearchPaginator(search_results, RESULTS_PER_PAGE)
            else:
                self.warn_no_results = True
        
        self.get_results()
    
        self.set_template_data()
        
        if settings.DEBUG:
            logger.info(">>>>>>>>>>>>> Cleaned search session key %s" % self.search_key)
        
        if settings.DEBUG:
            elapsed_time = time() - bench_start
            logger.info("Ran Search in %0.5f seconds" % elapsed_time)
        
        # cleanup temp memory search key cache
        clean_cache_search_key(self.search_key)
        
        # assign render results to cache
        assign_cache_search_render(self.search_key, self.get_render_data())


    def paginated_sorted_search(self, request, near, **kwargs):
        '''
        Similar to sorted_search, but instead of returning an array,
        it returns a Paginator object.
    
        You can pass options the following named arguments as kwargs:
            - distance: distance from near. Default is DEFAULT_DISTANCE)
            - current_location_text: See sorted_search. Default is None
            - per_page: The number of objects per page. Default is 10
            - max_pages: The maximum number of pages to display
        '''
        per_page              = kwargs.pop('per_page', RESULTS_PER_PAGE)
        distance              = kwargs.pop('distance', DEFAULT_DISTANCE)
        current_location_text = kwargs.pop('current_location_text', None)
        max_pages             = kwargs.pop('max_pages', int(MAX_MAP_RESULTS/RESULTS_PER_PAGE))
        start_time            = kwargs.pop('start_time', None)
        end_time              = kwargs.pop('end_time', None)
        
        search_key = kwargs.get('search_key', None)
        
        max_results = per_page * max_pages
        
        if max_results > MAX_MAP_RESULTS:
            logger.warning('per_page + max_pages is larger than the maximum displayable on the map.')
        
        if CACHE_SEARCH_KEY_SORT and search_key != None and search_key in _search_key_sort_results:
            results = _search_key_sort_results[search_key]
            logger.info('---------- sending cached sort - '+search_key)
        else:
            results = _sorted_search(request=request, near=near, distance=distance, max_results=max_results,
                                     current_location_text=current_location_text, 
                                     start_time=start_time, end_time=end_time,
                                     keyword=self.user_data.get('search_keyword', ''),
                                     **kwargs)
            
            
            
            if CACHE_SEARCH_KEY_SORT:
                _search_key_sort_results[search_key] = results
        
        return SearchPaginator(results, per_page)



    def assign_template_data(self):
        
        top_vehicles_length = 6
        top_admin3s_length = 9
        
        # set top ten vehicles
        if 'item' in self.data and len(self.data['item']) > 25:
            
            pa_ids = self.data['item'].keys()
            
            pa_rankings = Item.objects.filter(id__in=pa_ids).order_by('-order').values_list('id')[0:top_vehicles_length]
            
            self.template_vars['top_pa_list'] = Item.objects.filter(id__in=pa_rankings).order_by('-order')
        
        # set top admin3s
        if 'admin3' in self.data and len(self.data['admin3']) > 30:
            # sort admin3 list by count
            sorted_dict = SortedDict()
            admin3_list = sorted(self.data['admin3'].iteritems(), key=lambda (k,v): (v,k), reverse=True)[0:top_admin3s_length]
            for kv in admin3_list:
                sorted_dict[kv[0]] = kv[1]
            print sorted_dict
            self.template_vars['top_admin3_list'] = sorted_dict

        # assign all data keys
        if self.data:
            
            for key in self.data:
                
                if key:
                    # sort by name
                    sorted_keys = self.data[key].keys()
                    sorted_keys.sort()
                    sorted_dict = SortedDict()
                    for k in sorted_keys:
                        sorted_dict[k] = self.data[key][k]
                    
                    self.template_vars[ slugify(key).replace('-','_')] = sorted_dict
                else:
                    self.template_vars[ slugify(key).replace('-','_')] = self.data[key]
    
    def global_location(self):
        return global_location()
    
    def parse_location(self, text):
        return parse_location(text)
    
    
    def get_location(self):

        # define if we geocode or if we reverse geocode
        if self.user_data.get('search_lat') and self.user_data.get('search_lng'):
            try:
                address = AbstractLocation(latitude = float(self.user_data['search_lat']),
                                 longitude = float(self.user_data['search_lng']))
            
            except ValueError:
                address = self.global_location()
                messages.warning(self.request, ugettext(u"Lat/Long incorrects."))
        
        elif self.user_data.get('search_input'):
            # the request is driven by user using the search forms
            # get_address
            address = self.parse_location(self.user_data['search_input'])
        else:
            # finally we try to guess the user location address ?
            address = self.global_location()
        
        self.address = address

        if self.user_data.get('search_radius', ''):
            try:
                self.search_distance = int(self.user_data['search_radius'])
            except ValueError:
                try:
                    self.search_distance = int(round(float(self.user_data['search_radius'])))
                except ValueError:
                    self.search_distance = self.get_default_radius_meters(self.address)
        else:
            self.search_distance = self.get_default_radius_meters(self.address)
        
        # set min/max search radius
        self.skip_search = self.search_distance > MAX_SEARCH_RADIUS
        self.search_distance = max(min(self.search_distance, MAX_SEARCH_RADIUS), MIN_SEARCH_RADIUS)
    
    def get_default_radius_meters(self, location):
        return 20000
    
    def get_dates(self):
        
        start_time_string = ''
        end_time_string = ''
        
        if 'start_date' in self.user_data and 'start_hour' in self.user_data:
            start_time_string = self.user_data['start_date']+' '+self.user_data['start_hour']
        if 'end_date' in self.user_data and 'end_hour' in self.user_data:
            end_time_string = self.user_data['end_date']+' '+self.user_data['end_hour']
        
        start_time_tz = start_datetimetz_from_string(start_time_string)
        end_time_tz = end_datetimetz_from_string(end_time_string)
        
        min_reservation_m = getattr(settings, 'MIN_DATE_FRAME_DURATION', 30)
        max_reservation_m = getattr(settings, 'MAX_DATE_FRAME_DURATION', 86400)
        
        if end_time_tz <= start_time_tz + datetime.timedelta(minutes=min_reservation_m):
            end_time_tz = start_time_tz + datetime.timedelta(days=1)
        
        if end_time_tz > start_time_tz + datetime.timedelta(minutes=max_reservation_m):
            end_time_tz = start_time_tz + datetime.timedelta(days=1)
            
        self.start_time_tz = start_time_tz
        self.end_time_tz = end_time_tz
        
        self.start_time = self.start_time_tz
        self.end_time = self.end_time_tz

        
    def get_filters(self):
        """
        Call the different filter types
        Override to create special filters
        """
        self.get_sorting()
        self.get_type_filters()
        self.get_max_age_filters()
        
    
    def get_type_filters(self):
        
        TYPES = []
        
        types_array = []
        
        for itype in TYPES:
            
            if 'type_'+itype in self.user_data \
                and self.user_data['type_'+itype] == 'on':
                types_array.append(itype)
        
        
        if len(types_array):
            self.filters['item__type__in'] = types_array
        
    
    
    def get_max_age_filters(self):
        
        if 'max_age' in self.user_data and self.user_data['max_age']:
            max_age = int(self.user_data['max_age'])
            if max_age > 0:
                actual_year = datetime.datetime.now().year
                max_year = actual_year - max_age
                self.filters['item__created_date__gte'] = max_year
    
       
    def get_sorting(self):
        
        if 'search_sort_by' in self.user_data and self.user_data['search_sort_by'] in SORT_OPTIONS:
            self.filters['sort_by'] = self.user_data['search_sort_by']
        else:
            self.filters['sort_by'] = ''

        if 'search_display_unvisible' in self.user_data and self.user_data['search_display_unvisible'] == 'on':
            self.show_all_nodes = True
        else:
            self.show_all_nodes = False
        
        
    def get_results(self):
        
        if not self.search_results:
            return 
        
        if not 'page' in self.user_data:
            self.user_data['page'] = 1
            
        paged_results = None
        try:
            paged_results = self.search_results.page(self.user_data['page'])
        except EmptyPage:
            # We tried to access a page too far.  (Via search engine, vehicles deactivated 
            # during request, etc.)  Jump back to page 1, which is allowed to be empty.
            page = 1
            paged_results = self.search_results.page(page)
            self.user_data['page'] = page
        
        self.paged_results = paged_results
        
        
        
    def search_filters_handler(self):
        
        user_data = get_search_session_vars(self.request)
        
        self.template_vars['user_input_form'] = UserInputForm(initial=user_data)
        #self.template_vars['search_form'] = SearchSettingsForm(initial=user_data)
        self.template_vars['type_form'] = SearchTypesForm(initial=user_data)
        self.template_vars['age_form'] = SearchAgeForm(initial=user_data)
        
        search_filter_forms = ( #self.template_vars['search_form'],
                                #self.template_vars['type_form'],
                                #self.template_vars['age_form']
                                )
        
        self.template_vars['search_filter_forms'] = search_filter_forms
        
        # Render the template and return it
        return render_to_string('search/filters.html', dictionary=self.template_vars, context_instance=RequestContext(self.request))
        
    def filters_applied_handler(self):
        
        applied_filters = []
        applied_filters = get_applied_form_filters(applied_filters,SearchInputForm(initial={}),self.template_vars['search_input_form'])
        applied_filters = get_applied_form_filters(applied_filters,SearchKeywordForm(initial={}),self.template_vars['search_keyword_form'])
        
        applied_filters = get_applied_form_filters(applied_filters,SearchSettingsForm(initial={}),self.template_vars['search_form'])
        applied_filters = get_applied_form_filters(applied_filters,SearchTypesForm(initial={}),self.template_vars['type_form'])
        
        applied_filters = get_applied_form_filters(applied_filters,SearchAgeForm(initial={}),self.template_vars['age_form'])
        
        self.template_vars['applied_filters'] = applied_filters
        
        # Render the template and return it
        return render_to_string('search/applied.html', dictionary=self.template_vars, context_instance=RequestContext(self.request))
    
    
    def build_page_title(self):
        
        label_type = _search_drilldown_cache.guess_type_from_data(self.path_key)
        return drilldown_item_title( self.path_key, label_type )
        
    def build_page_header(self):
        
        return render_to_string('search/header.html', dictionary=self.template_vars, context_instance=RequestContext(self.request))
    
    def build_page_content(self):
        
        item = None
        
        if self.path_key:
            try:
                item = Item.objects.get_at_url(self.path_key, exact=True)
            except ObjectDoesNotExist:
                pass
        else:
            try:
                item = Item.objects.get_at_url(self.request.path_info, exact=True )
            except ObjectDoesNotExist:
                pass
        
        if item and item.is_visible():
            self.template_vars['item'] = item
        
        return render_to_string('search/content.html', dictionary=self.template_vars, context_instance=RequestContext(self.request))
        
    def build_search_banner(self):
        
        user_data = self.user_data
        template_vars = self.template_vars
        
        template_vars['search_keyword_form'] = SearchKeywordForm(initial=user_data)
        template_vars['search_input_form'] = SearchInputForm(initial=user_data)
        template_vars['search_form'] = SearchSettingsForm(initial=user_data)
        
        
        return render_to_string('search/banner.html', dictionary=self.template_vars, context_instance=RequestContext(self.request))
    
    def drilldown_selection_handler(self):
        
        return render_to_string('search/drilldown.html', dictionary=self.template_vars, context_instance=RequestContext(self.request))
    
    
    def search_selection_handler(self):
        '''
        Given a request and a list of ParkingAddresses, view the selection list.  Returns HTML.
        Pass in search results from ajax or view.
        '''
        
        try:
            page_count = self.search_results.num_pages
        except:
            return render_to_string('search/list.html', dictionary=self.template_vars, context_instance=RequestContext(self.request))
        
        if int(self.user_data['page']) <= page_count:
            page = self.user_data['page']
        else:
            page = 1
            self.user_data['page'] = 1
        
        current_page = self.search_results.page(page)
        
        template_vars = self.template_vars
        template_vars['current_page'] = current_page
        template_vars['paginator'] = self.search_results
        
        template_vars['page'] = page
        
        template_vars = self.get_paginator_root_path(self.path, template_vars)
        
        template_vars['sort_form'] = SearchSortForm(initial=self.user_data)
        template_vars['page_form'] = SearchPageForm(initial=self.user_data)
        
        template_vars['user_data'] = self.user_data
        
        template_vars['search_max_results'] = self.max_results
        template_vars['search_distance'] = self.search_distance
        template_vars['search_distance_str'] = pretty_distance(self.search_distance, units) if units else _(u'map area')
        
        self.parse_json_data(self.search_results)
        
        template_vars['json_data'] = self.json_data_string
        
        self.template_vars = template_vars
        
        # Render the template and return it
        return render_to_string('search/list.html', dictionary=template_vars, context_instance=RequestContext(self.request))

    
    def parse_json_data(self, parking_address_paginator):
        
        self.json_data = {}
        #self.json_data['lat'] = self.address.latitude
        #self.json_data['long'] = self.address.longitude
        #self.json_data['radius'] = self.search_distance
        #self.json_data['results'] = []
        self.json_data['points'] = []
        
        if self.search_key in _search_key_points:
            self.json_data['points'] = _search_key_points[self.search_key]
            del _search_key_points[self.search_key]
        
        self.json_data_string = json.dumps(self.json_data)
        
        
    
    def set_template_data(self):
        
        self.assign_template_data()
        
        self.template_vars = self.get_paginator_root_path(self.path, self.template_vars)

        self.template_vars['user_data'] = self.user_data
        self.template_vars['search_key'] = self.search_key
        self.template_vars['search_path'] = self.path_key
        
        self.template_vars['search_path'] = self.path_key
        
        if settings.DEBUG:
            self.template_vars['user_data_json'] = json.dumps(self.user_data)
            
            self.template_vars['directory_update'] = 'now'
            self.template_vars['directory_path'] = self.path_key
            self.template_vars['directory_json'] = json.dumps(self.data)
        
        self.template_vars['start_time'] = self.start_time_tz
        self.template_vars['end_time'] = self.end_time_tz
        
        self.template_vars['address'] = self.address
        #self.template_vars['pretty_duration'] = self.pretty_duration
        
        self.template_vars['search_filters_snippet'] = self.search_filters_handler()
        
        self.template_vars['warn_no_results'] = self.warn_no_results
        
        self.template_vars['car_selection_snippet'] = self.search_selection_handler()
        self.template_vars['drilldown_selection_snippet'] = self.drilldown_selection_handler()
        
        self.template_vars['page_title_snippet'] = self.build_page_title()
        self.template_vars['page_header_snippet'] = self.build_page_header()
        self.template_vars['page_content_snippet'] = self.build_page_content()
        self.template_vars['search_banner_snippet'] = self.build_search_banner()
        
        self.template_vars['filters_applied_snippet'] = self.filters_applied_handler()
    def get_render_data(self):
        
        render_data = {}
        
        render_data['search_filters_snippet'] = self.template_vars['search_filters_snippet']
        render_data['filters_applied_snippet'] = self.template_vars['filters_applied_snippet']
        
        render_data['warn_no_results'] = self.template_vars['warn_no_results']
        
        render_data['car_selection_snippet'] = self.template_vars['car_selection_snippet']
        render_data['drilldown_selection_snippet'] = self.template_vars['drilldown_selection_snippet']
        
        render_data['page_title_snippet'] = self.template_vars['page_title_snippet']
        render_data['page_header_snippet'] = self.template_vars['page_header_snippet']
        render_data['page_content_snippet'] = self.template_vars['page_content_snippet']
        render_data['search_banner_snippet'] = self.template_vars['search_banner_snippet']
        
        return render_data
        
        



    def get_paginator_root_path(self, path, template_vars):
        '''
        Retreives the searched root path to compose paginator urls
        '''
        template_vars['page_root_path'] = ''
        template_vars['dd_request_path'] = path
        
        return template_vars


def build_extra_search_kwargs(start_time, end_time, estimated_distance, filters=None):
    '''
    Given the base filters returned by build_filters_from_get_data and the 
    start/end/distance for this reservation, build some additional kwargs needed
    by the sorted_search method.  May return an empty dict if no extra kwargs are
    required.
    '''
    if not filters:
        filters = {}
    search_kwargs = filters.copy()
    
    if start_time and end_time:
        search_kwargs['start_time'] = start_time
        search_kwargs['end_time'] = end_time

    if search_kwargs.get('sort_by', None) in ('cheapest', 'most_expensive'):
        search_kwargs['sort_comparison_method'] = comparison_function_for_estimated_cost({
            'start_datetime': start_time,
            'end_datetime': end_time,
            'distance': estimated_distance
        })

        sort_by = search_kwargs.pop('sort_by')
        if sort_by == 'most_expensive':
            search_kwargs['reverse_results'] = True

    return search_kwargs

class AbstractLocation(object):
    
    def __init__(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude
    
    def __unicode__(self):
        return str(self.latitude)+':'+str(self.longitude)

def global_location():
    return AbstractLocation(0,0)
    
def parse_location(text):
    '''
    Given some text representing a location, parse it and return an AbstractLocation.
    
    Text can be:
        - an object, instance of AbstractAddress
        - a latitude and longitude pair, comma-separated
        - a text address string, suitable for geocoding
        
    Throws a RuntimeError if it can't parse successfully.
    '''
    #print text
    
    if not text:
        raise ValueError(_(u'Must provide a valid address to parse:%s' % text))
    
    if isinstance(text, AbstractLocation):
        location = text
    else:
        text_slug = slugify(text)
        if _search_drilldown_cache.has_object('label', text_slug):
            location_object = _search_drilldown_cache.get_object('label', text_slug)
            
            print location_object
            
            location = AbstractLocation(float(location_object['stats']['lat']), float(location_object['stats']['lng']) )
            
        elif _search_drilldown_cache.has_key(text_slug):
            
            # location is known and handled by a uid
            location_data = _search_drilldown_cache.get_key_data(text_slug)
            
            location_object = _search_drilldown_cache.get_object('item', location_data['item'].keys()[0])
            
            print location_object
            
            location = AbstractLocation(float(location_object['data']['lat']), float(location_object['data']['lng']) )
            
        else:
            if text[0] != '/':
                text = slugify(text)
            try:
                location = Item.objects.get_at_url(text, exact=False)
                return AbstractLocation(location.latitude, location.longitude)
            except ObjectDoesNotExist:
                location = global_location()
            #return location
        
        logger.debug("text is Location = %s" % location)
    
    if not location:
        raise RuntimeError(_(u'Unable to use this location: %s') % text)
    
    return location


'''
Search methods
'''
def _search(request, near, distance=DEFAULT_DISTANCE, keyword='', **kwargs):
    '''
    Given a circle with a radius in meters ("distance") and a string that represents
    the centroid ("near"), return a list of ParkingAddress objects that are contained 
    within the circle.  The centroid can be either a geocodable address, a UserAddress uid,
    an instance of AbstractAddress, or a latitude/longitude pair.
    
    ParkingAddress objects attached to inactive vehicles are excluded.
    
    Will raise RuntimeError if an invalid UserAddress uid is provided or an address
    string can't be geocoded.
    
    This method tries hard to NOT evaluate the QuerySet, in case you are only interested
    in a subset of it and can benefit from some in-database paging.
    '''
    location = parse_location(near)
    
    results = Item.objects.near(location, distance)
    
    # Create a ParkingAddressSearchQuerySet, which remembers the search options 
    # for later slicing/sorting
    
    exclude = kwargs.pop('exclude', {})
    if exclude:
        results = results.exclude(**exclude)
    if kwargs:
        results = results.filter(**kwargs)
    
    if keyword:
        fieldnames = ['slug__contains', 
                      'label__contains', 
                      'title__contains', 
                      'description__contains', 
                      'content__contains',
                      ]
        
        qgroup = reduce(operator.or_,
                        (Q(**{fieldname: keyword}) for fieldname in fieldnames))
    
        results = results.filter(qgroup)

    results = results._clone(klass=results.__class__)
    
    results.search_options['location'] = request.location = location
    results.search_options['distance'] = request.distance = distance
    results.search_options['request'] = request
    
    return results


def _sorted_search(request, near, distance=DEFAULT_DISTANCE, max_results=MAX_SORT_RESULTS,
                   current_location_text=None, keyword='', start_time=None, end_time=None, **kwargs):
    '''
    Internal sorted search method.
    '''
    if settings.DEBUG:
        bench_start = time()
    
    sort_key_method = kwargs.pop('sort_key_method', None)
    sort_comparison_method = kwargs.pop('sort_comparison_method', None)
    reverse_results = kwargs.pop('reverse_results', False)
    
    search_key = kwargs.pop('search_key', None)
    show_all_nodes = kwargs.pop('show_all_nodes', False)
    
    # If necessary, pass the appropriate sort method
    if 'sort_by' in kwargs and not sort_comparison_method and not sort_key_method:
        sort_comparison_method = sorted_search_comparison_for_sort_option(kwargs.pop('sort_by'))
    
    # Build the raw search
    parking_address_results = _search(request, near, distance, keyword, **kwargs)
    
    # Add filter on vehicle reservation minimum if times are present
    
    #if not show_all_nodes and start_time and end_time:
    #    parking_address_results = parking_address_results.filter(vehicle__min_reservation_hours__lte=duration_minutes(start_time, end_time) // 60)

    # db ordering by distance is helpful for most sorts, but not for large distances
    # where we want "random" results to fill our map
    if distance < DEFAULT_DISTANCE_CITY:
        parking_address_results = parking_address_results.order_by('distance')

    #if not parking_address_results.is_empty:
        # Constrain results for performance - this screws up sorting so TODO
    parking_address_results = parking_address_results[:max_results]

    parking_address_results = _sort_search_results(parking_address_results,
                                                   sort_key_method=sort_key_method,
                                                   sort_comparison_method=sort_comparison_method,
                                                   reverse_results=reverse_results)

    # Copy some additional parameters onto the QuerySet for later slicing/sorting
    parking_address_results.search_options['current_location'] = current_location_text
    parking_address_results.search_options['start_time'] = start_time
    parking_address_results.search_options['end_time'] = end_time
    parking_address_results.search_options['search_key'] = search_key
    parking_address_results.search_options['show_all_nodes'] = show_all_nodes
    
    if settings.DEBUG:
        elapsed_time = time() - bench_start
        logger.info("Sorted search took a total of %0.5f seconds" % (elapsed_time))
        
    return parking_address_results

def _objects_from_search_results(search_results, start=0, end=None):
    '''
    Given a (typically partial) set of search results, build first-class
    ORM instances from them and add all the availability, distance, etc.
    that is useful for display.
    '''
    if settings.DEBUG:
        bench_start = time()

    if not hasattr(search_results, 'search_options'):
        raise AttributeError('Missing search_options attribute on search results.')
    
    location = search_results.search_options['location']
    request = search_results.search_options['request']
    start_time = search_results.search_options.get('start_time', None)
    end_time = search_results.search_options.get('end_time', None)
    current_location = search_results.search_options.get('current_location', None)

    # Build and attach child objects    
    ids = [p.id for p in search_results[start:end]]
    pa_qs = Item.objects.filter(id__in=ids)
    
    # Add distance calculations
    _cache_distance(request, pa_qs, location, current_location)

    # Sort list in original order
    sorted_pa_qs = [None] * len(ids)
    for pa in pa_qs:
        sorted_pa_qs[ids.index(pa.id)] = pa

    if settings.DEBUG:
        elapsed_time = time() - bench_start
        logger.info("_objects_from_search_results call took a total of %0.5f seconds" % (elapsed_time))

    return sorted_pa_qs


def _objects_n_count_from_search_results(search_results, start=0, end=None):
    '''
    Extension of the original _objects_from_search_results to filter unavailable vehicles and retrive count
    '''
    if settings.DEBUG:
        bench_start = time()
        
    if not hasattr(search_results, 'search_options'):
        raise AttributeError('Missing search_options attribute on search results.')
    
    location = search_results.search_options['location']
    request = search_results.search_options['request']
    start_time = search_results.search_options.get('start_time', None)
    end_time = search_results.search_options.get('end_time', None)
    current_location = search_results.search_options.get('current_location', None)
    
    search_key = search_results.search_options.get('search_key', None)
    
    show_all_nodes = search_results.search_options.get('show_all_nodes', False)
   
    if CACHE_SEARCH_KEY_PAGE and search_key in _search_key_page_results:
        return _search_key_page_results[search_key]
    
    ids = [p.id for p in search_results]
    coords = []
    
    
    # pre request result ids
    pa_qs = Item.objects.filter(id__in=ids)
    
    
    """
    # overlap_status to check if vehicle is unavailable because of confirmed reservation
    overlap_status = ['accepted', 'confirmed', 'error']
    # Build and attach child objects
    if not show_all_nodes and start_time and end_time:
        
        # Add availability
        if start_time and end_time:
            pa_qs = annotate_availability(pa_qs, 
                                          shift_to_local_time(start_time), 
                                          shift_to_local_time(end_time))
        
        if not show_all_nodes:
            for p in pa_qs: 
                if not p.available:
                    ids.remove(p.id)
                else:
                    if ReservationVehicle.objects.overlapping_time(shift_to_local_time(start_time), shift_to_local_time(end_time), vehicle=p.vehicle).filter(status__in=overlap_status).count():
                        ids.remove(p.id)
        
        if search_key and settings.DEBUG:
            logger.info("RESULTS: %s/%s - %s" % (len(ids),len(search_results),search_key))
    """
    filtered_count = len(ids)
    ids = ids[start:end]
    
    for p in pa_qs:
        coords.append((p.latitude, p.longitude, p.id))
    
    if search_key != None:
        _search_key_points[search_key] = coords
    
    pa_qs = Item.objects.filter(id__in=ids)
    
    # Add distance calculations
    _cache_distance(request, pa_qs, location, current_location)
    
    # Sort list in original order
    sorted_pa_qs = [None] * len(ids)
    for pa in pa_qs:
        sorted_pa_qs[ids.index(pa.id)] = pa
    
    if settings.DEBUG:
        elapsed_time = time() - bench_start
        logger.info("_objects_from_search_results call took a total of %0.5f seconds" % (elapsed_time))
    
    if CACHE_SEARCH_KEY_PAGE and search_key != None:
        _search_key_page_results[search_key] = sorted_pa_qs
    
    final_pa_qs = []
    for node in sorted_pa_qs:
        final_pa_qs.append(node.item)
    
    return final_pa_qs, filtered_count


def sorted_search(request, near, **kwargs):
    '''
    Calls search, but sorts results by distance from near (and adds distance and distance_from_center 
    attributes to each address.  These attributes are the same unless you provide a current_location_text.
    If current_location_text is provided, the distance attribute is the distance to the current_location, 
    and not near.  
    
    You can pass options the following named arguments as kwargs:
        - distance: distance from near. Default is DEFAULT_DISTANCE)
        - current_location_text: See sorted_search. Default is None
        - max_results: The maximum number of results to return.  Default is 20
        - sort_key_method: A custom sort method for ordering results.  This should be the method itself, 
            not a string.  See _sort_search_results for details.
    '''
    distance              = kwargs.pop('distance', DEFAULT_DISTANCE)
    current_location_text = kwargs.pop('current_location_text', None)
    max_results           = kwargs.pop('max_results', RESULTS_PER_PAGE)
    start_time            = kwargs.pop('start_time', None)
    end_time              = kwargs.pop('end_time', None)
    results = _sorted_search(request=request, near=near, 
                             distance=distance, 
                             max_results=max_results,
                             current_location_text=current_location_text, 
                             start_time=start_time, end_time=end_time, **kwargs)
    
    return _objects_from_search_results(search_results=results)



'''
Cache Methods

These take a queryset of ParkingAddress results and populate data that is too 
complex or expensive to include in the initial query
'''
def _cache_distance(request, parking_address_results, search_location, current_location=None):
    ''' 
    Do some additional distance computations useful for sorting and display.
    '''
    search_location = parse_location(search_location)
    
    if current_location:
        try:
            current_location = parse_location(current_location)
        except RuntimeError:
            pass

    distances = []
    for parking_address in parking_address_results:
        parking_address.distance_from_center = geopy.distance.distance(
                      (search_location.latitude, search_location.longitude),
                      (parking_address.latitude, parking_address.longitude)).meters
        
        # Only need to recompute distance if it's in relation to a different location
        if current_location:
            parking_address.distance = geopy.distance.distance(
                      (current_location.latitude, current_location.longitude),
                      (parking_address.latitude, parking_address.longitude)).meters
        else:
            parking_address.distance = parking_address.distance_from_center

        # also round to nearest 50m
        parking_address.rounded_distance = round_to(parking_address.distance, 50)
        parking_address.rounded_distance_from_center = round_to(parking_address.distance_from_center, 50)

        distances.append(parking_address.distance)

    # Potentially resize request.distance with a more accurate bound for these results 
    if len(distances) > 0:
        request.distance = min(max(distances)*1.1, request.distance)



def _add_to_search_queryset_requirements(search_qs, sort_method):
    '''
    Given the search QuerySet and a sort method, add any additional requirements
    the default search and custom sort method will need to select to behave properly.
    '''
    sort_qs_requires = getattr(sort_method, 'queryset_requires', {})
    
    qs_reqs = _merge_search_queryset_requirements(_search_queryset_requires, sort_qs_requires)
    
    for qs_type in _search_queryset_requires_valid_options:
        if qs_type in qs_reqs:
            search_qs = getattr(search_qs, qs_type)(*qs_reqs[qs_type])

    return search_qs


def _sort_search_results(results, sort_key_method=None, sort_comparison_method=None, reverse_results=False):
    '''
    With a given resultset ("results"), sort them according to their distance from
    "sort_around_location", and add the attribute "distance", which contains the distance
    from either "sort_around_location" or "current_location" (if provided). The attribute
    "distance_from_center" is always the distance from "sort_around_location".
    
    If you want a different sort method, provide a method for either "sort_key_method" in the 
    sorted "key" format or "sort_comparison_method" in the sorted comparison format.

    "sort_key_method" should take a single argument (ParkingAddress), and return a 
    numeric key to sort on, smallest to largest.

    "sort_comparison_method" should take two arguments (ParkingAddress), and return -1, 0, or 1,
    depending on whether the first argument is smaller than, equal to, or bigger than the second
    argument respectively.
    '''
    if settings.DEBUG:
        bench_start = time()

    #if results.is_empty:
    #    return results

    # Add any additional select_required / only fields needed by sort
    results = _add_to_search_queryset_requirements(results, sort_key_method \
                                                     or sort_comparison_method \
                                                     or _default_sort_comparison)
        
    # Now run sort method
    if sort_key_method:
        sorted_results = sorted(results, key=sort_key_method)
        sort_method_name = sort_key_method.__name__
    elif sort_comparison_method:
        sorted_results = sorted(results, cmp=sort_comparison_method)
        sort_method_name = sort_comparison_method.__name__
    else:
        sorted_results = sorted(results, cmp=_default_sort_comparison)
        sort_method_name = _default_sort_comparison.__name__
    
        
    if reverse_results:
        sorted_results.reverse()

    # Now stuff the toothpaste back in the tube so to speak.  This allows us to continue
    # to reference the ParkingAddressSearchQuerySet.
    results._iter = None
    results._result_cache = sorted_results
    
    if settings.DEBUG:
        elapsed_time = time() - bench_start
        logger.info("Sorting (%s) took %0.5f seconds for %s results" % (sort_method_name, elapsed_time, len(results)))

    return results

class ItemPaginator(Paginator):
    pass

class SearchPaginator(Paginator):
    '''
    Custom Paginator that populates Vehicle rates and child objects for presentation
    '''
    def __init__(self, *args, **kwargs):
        super(SearchPaginator, self).__init__(*args, **kwargs)
        self.page_cache = {}

    def raw_page(self, number):
        return super(SearchPaginator, self).page(number)

    def page(self, number):
        "Returns a Page object for the given 1-based page number."
        number = self.validate_number(number)
        try:
            if number not in self.page_cache:
                bottom = (number - 1) * self.per_page
                top = bottom + self.per_page
                if top + self.orphans >= self.count:
                    top = self.count
                
                pa_qs, self._count = _objects_n_count_from_search_results(search_results=self.object_list, start=bottom, end=top) 
                
                self.page_cache[number] = Page(pa_qs, number, self)
        except:
            return Page(self.object_list, number, self)
        
        return self.page_cache[number]


def _address_and_admin3_equal(address):
    '''
    Google and other geocoders can screw with the spelling of our admin3 depending upon 
    the language of our request, so this is not foolproof.
    '''
    if not address or not hasattr(address, 'full_address') \
      or not address.full_address or not address.admin3:
        return False
    admin3_test = unicodedata.normalize('NFKD', address.admin3).encode('ascii','ignore')
    address_test = unicodedata.normalize('NFKD', address.full_address).encode('ascii','ignore')
    return address_test == admin3_test

def default_radius_meters(address=None):
    '''
    Returns the default distance (in meters) from the centroid for vehicles searches.
    
    If given an optional address it will return a larger area for less precise addresses.
    '''
    if address and hasattr(address, 'full_address'):
        if _address_and_admin3_equal(address):
            return DEFAULT_DISTANCE_CITY
        elif address.admin0 and not address.admin3:
            return DEFAULT_DISTANCE_COUNTRY
    
    return DEFAULT_DISTANCE

def distance_until_no_zoom(address=None):
    '''
    Returns the distance (in meters) at which you should stop zooming out while searching
    for cars.
    
    If given an optional address it will return a larger area for less precise addresses.
    '''
    if address and hasattr(address, 'full_address'):
        if _address_and_admin3_equal(address):
            return DEFAULT_DISTANCE_UNTIL_NO_ZOOM_CITY
        elif address.admin0 and not address.admin3:
            return DEFAULT_DISTANCE_UNTIL_NO_ZOOM_COUNTRY
        
    return DEFAULT_DISTANCE_UNTIL_NO_ZOOM

def results_until_no_zoom(address=None):
    '''
    Returns the default distance (in meters) from the centroid for vehicles searches.
    
    If given an optional address it will return a larger area for less precise addresses.
    '''
    if address and hasattr(address, 'full_address'):
        if _address_and_admin3_equal(address):
            return RESULTS_UNTIL_NO_ZOOM_CITY
    
    return DEFAULT_RESULTS_UNTIL_NO_ZOOM





'''
Comparison methods
'''
_search_queryset_requires_valid_options = ['only', 'select_related']
_search_queryset_requires_valid_booleans = ['cache_item_pricing']

def _merge_search_queryset_requirements(*qs_dicts):
    qs_reqs = {}
    for qs_type in _search_queryset_requires_valid_options:
        qs_opts = set()
        for qs_dict in qs_dicts:
            qs_opts.update(qs_dict.get(qs_type, []))
        if qs_opts:
            qs_reqs[qs_type] = qs_opts
    for qs_type in _search_queryset_requires_valid_booleans:
        qs_val = None
        for qs_dict in qs_dicts:
            if qs_type in qs_dict and qs_val is None or qs_val == False:
                qs_val = qs_dict[qs_type]
        if qs_val is not None:
            qs_reqs[qs_type] = qs_val
    return qs_reqs


# Common select_related and fields that all search comparisons require
_search_queryset_requires = {
    'select_related': [],
    'only': ['id', 'latitude', 'longitude']
}

def compare_addresses_by_distance_from_center(address1, address2):
    '''
    Comparison function that uses distance_from_center to compare.
    '''
    if hasattr(address1, 'distance_from_center') and hasattr(address2, 'distance_from_center'):
        return cmp(address1.distance_from_center, address2.distance_from_center)
    return cmp(address1.distance, address2.distance)

compare_addresses_by_distance_from_center.queryset_requires = {}



def compare_addresses_by_created_date(address1, address2):
    '''
    Compares addresses based on created date, newest first.
    '''
    return cmp(address2.created_date, address1.created_date)

compare_addresses_by_created_date.queryset_requires = {
    'only': ['created_date',],
}


def compare_addresses_by_order(address1, address2):
    '''
    Compares addresses based on stored search ranking. Higher number is better.
    '''
    return cmp(address2.order, address1.order)

compare_addresses_by_order.queryset_requires = {
    'only': ['order',],
}


def comparison_function_for_estimated_cost(cost_kwargs):
    '''
    Given a set of cost_kwargs, this returns a comparator function
    for use when sorting search results. It uses add_estimated_cost
    to calculate the cost.
    '''
    def compare_addresses_by_estimated_cost(address1, address2):
        add_estimated_cost(address1, cost_kwargs)
        add_estimated_cost(address2, cost_kwargs)

        return cmp(address1.estimated_cost, 
                   address2.estimated_cost)

    compare_addresses_by_estimated_cost.queryset_requires = {
        'only': ['admin0'],#['admin0', 'vehicle__fuel_economy', 'vehicle__fuel_type',],
        'select_related': []
    }

    return compare_addresses_by_estimated_cost


def _default_sort_comparison(address1, address2):
    # Order that various properties should be compared.
    # We start at the first one, and if that is not 0, return the
    # result of that comparison. If it's 0, we proceed to the next
    # comparison

    comparisons = (
        compare_addresses_by_order,
        compare_addresses_by_distance_from_center,
    )

    for comparison in comparisons:
        result = comparison(address1, address2)
        if result != 0:
            return result

    # They're equal if it gets to this point
    return 0

_default_sort_comparison.queryset_requires = \
    _merge_search_queryset_requirements(compare_addresses_by_order.queryset_requires, 
                                        compare_addresses_by_distance_from_center.queryset_requires
                                        )


def sorted_search_comparison_for_sort_option(sort_option):
    '''
    For a given sort option (from SORT_OPTIONS), returns a comparator function for sorting.
    '''
    if not sort_option in SORT_OPTIONS:
        return _default_sort_comparison

    if sort_option == 'closest':
        comparator = compare_addresses_by_distance_from_center
    elif sort_option == 'newest':
        comparator = compare_addresses_by_created_date
    else:
        # Other sort options must be done in the view, so the appropriate cost
        # kwargs are passed, so just return the default.
        comparator = _default_sort_comparison

    # wrap the comparison function, so it can fallback to
    # the default sort order
    def final_comparator(address1, address2):
        result = comparator(address1, address2)
        if result == 0:
            # Fall back to default sort
            result = _default_sort_comparison(address1, address2)

        return result

    final_comparator.queryset_requires = _merge_search_queryset_requirements(comparator.queryset_requires,
                                                                             _default_sort_comparison.queryset_requires)
    return final_comparator



# DISABLED
def add_estimated_cost(parkingaddress, cost_kwargs):
    '''
    Given a ParkingAddress and kwargs needed to calculate the cost of a reservation, make
    the calculation and assign the result to the vehicle.estimated_cost attribute.
    
    This is used by the search views to provide an estimated cost when searching for vehicles. 

    If a price has already been estimated for the given vehicle, it will not be recalculated.
    Thus, it is safe to call this method multiple times with the same parkingaddress.
    '''
    parkingaddress.estimated_cost = 1
    return parkingaddress


