'''
Created on 5 nov. 2013

@author: rux
'''
from datetime import datetime, timedelta
import hashlib
from importlib import import_module
import json
import logging
import re
import traceback

from django.conf import settings
from django.core.cache import cache as search_cache
from django.utils import translation, timezone
from django.utils.timezone import now
from django.utils.translation import get_language

from apetizer.directory import _history_connector, _search_keys
from apetizer.directory.dates import datetimetz_from_string, \
    start_datetimetz_from_string, end_datetimetz_from_string
from apetizer.forms.search import SearchPageForm, SearchSortForm, \
    SearchInputForm, SearchSettingsForm, SearchAgeForm, SearchKeywordForm


logger = logging.getLogger(__name__)

SEARCH_KEY_NAME = 'skey'
SEARCH_COOKIE_NAME = 'user_data'
SEARCH_KEY_COOKIE_NAME = SEARCH_KEY_NAME

CACHE_SEARCH_KEY_DURATION = getattr(settings, 'CACHE_SEARCH_KEY_DURATION', 3600)
CACHE_SEARCH_KEY_SORT = getattr(settings, 'CACHE_SEARCH_KEY_SORT', False)
CACHE_SEARCH_KEY_PAGE = getattr(settings, 'CACHE_SEARCH_KEY_PAGE', False)

search_forms = (SearchPageForm, 
                SearchInputForm,
                SearchKeywordForm, 
                SearchSortForm, 
                SearchSettingsForm, 
                SearchAgeForm)


def get_form_filters(data):
    """
    filter data with search forms
    """
    field_dict = {}
    for formClass in search_forms:
        form = formClass(initial=data)
        for field in form:
            if field.name in data:
                if type(data[field.name]) != type(u''):
                    field_dict[field.name] = str(data[field.name])
                else:
                    field_dict[field.name] = data[field.name]
    
    return field_dict


def get_search_key(request):
    """
    get the current search key associated with the request
    """
    # get the search prior from get
    skey = request.GET.get('skey', None)

    # test if skey is hexadecimal
    if skey:
        try:
            int(skey, 16)
        except ValueError:
            return None
    else:
        # then get from session
        session_key = request.session.session_key
        skey = import_module(settings.SESSION_ENGINE).SessionStore(session_key=session_key).get(SEARCH_KEY_NAME, None)

        # still None,try to get it from cookie
        if skey is None:
            skey = request.COOKIES.get('skey', None)

    return skey


def get_actual_session_key(request):
    """
    get the current search key recorded in the request session
    """
    session_key = request.session.session_key
    s = import_module(settings.SESSION_ENGINE).SessionStore(session_key=session_key)
    skey = s.get(SEARCH_KEY_NAME, None)
    
    return skey


def get_key_filter(data):
    """
    filters key data 
    and calculates the skey hash
    """

    search_filters = get_form_filters(data)

    search_hash = json.dumps(search_filters)
    search_key = hashlib.md5(search_hash).hexdigest()
    
    return search_key, search_filters


def assign_cache_search_key( search_key, search_filters ):
    """
    assigns cache and in-memory dict search key data
    """
    # assign cache entry
    search_cache.set(search_key, search_filters, CACHE_SEARCH_KEY_DURATION)
    
    # assign temp thread entry
    _search_keys[search_key] = search_filters.copy()


def retrieve_cache_search_key(search_key):
    """
    gets search key data from the cache
    """
    # try to get from cache first
    search_filters = search_cache.get(search_key)

    # return local temp memory key
    if search_filters is None and search_key in _search_keys:
        search_filters = _search_keys[search_key].copy()
    
    return search_filters


def clean_cache_search_key(search_key):
    """
    cleanup temp memory search key cache
    """
    if search_key in _search_keys:
        del _search_keys[search_key]


def assign_cache_search_render(search_key, data):
    """
    assigns cache search render associated with skey
    """
    language = get_language()
    
    # assign cache entry
    search_cache.set(search_key+'-renders-'+language, data, CACHE_SEARCH_KEY_DURATION)


def get_cache_search_render(search_key):
    """
    gets cache search key render
    """
    data = None

    if search_key is not None:
        language = get_language()
        data = search_cache.get(search_key + '-renders-' + language)
    
    return data


def save_search_key(request, session_key, search_filters):
    """
    saves the search key
    """
    search_key, search_filters = get_key_filter(search_filters)

    # store only if not already in cache to preserve it's lifetime
    assign_cache_search_key(search_key, search_filters)

    # save session
    s = import_module(settings.SESSION_ENGINE).SessionStore(session_key=session_key)
    s[SEARCH_KEY_NAME] = search_key
    s.save()
    
    if session_key and search_cache.get(search_key + '-' + session_key) is None:
        # write to nosql
        try:
            _history_connector.put(search_key, session_key, search_filters)
            search_cache.set(search_key + '-' + session_key, True, CACHE_SEARCH_KEY_DURATION)
        except:
            logger.warning('Unable to write key ' + session_key)
            traceback.print_exc()
    
    return search_key



def _get_default_search_vars(default_start=None, default_end=None):
    """
    get's a default search session data dict
    """
    user_data = {}
    
    if default_start == None or type(default_start) != type(now()):
        start = now() + timedelta(days=1)
    else:
        start = default_start
        
    if default_end == None or type(default_end) != type(now()):
        end = start + timedelta(days=1)
    else:
        end = default_end
    
    current_language = translation.get_language()
    
    if current_language == 'en':
        start = start_datetimetz_from_string(get_rounded_time(start).strftime("%m/%d/%Y %H:%M"))
        end = end_datetimetz_from_string(get_rounded_time(end).strftime("%m/%d/%Y %H:%M"))
        
        user_data['start_date'] = start.strftime("%m/%d/%Y")
        user_data['end_date'] = end.strftime("%m/%d/%Y")
    else:
        start = start_datetimetz_from_string(get_rounded_time(start).strftime("%d/%m/%Y %H:%M"))
        end = end_datetimetz_from_string(get_rounded_time(end).strftime("%d/%m/%Y %H:%M"))
        
        user_data['start_date'] = start.strftime("%d/%m/%Y")
        user_data['end_date'] = end.strftime("%d/%m/%Y")
    
    user_data['search_input'] = ''
    user_data['search_path'] = ''
    user_data['search_tab'] = 'list'
    
    user_data['start_hour'] = start.strftime("%H:%M")
    user_data['end_hour'] = end.strftime("%H:%M")
    
    return user_data


def get_rounded_time(time_obj):
    """
    returns a half hour rounded time object
    """
    if time_obj.minute > 30:
        time_obj = time_obj.replace(minute=0)
        time_obj = time_obj + timedelta(hours=1)
    elif time_obj.minute == 0:
        pass
    else:
        time_obj = time_obj.replace(minute=30)
    
    return time_obj


def get_search_session_vars(request):
    """
    get's search data associated with a request
    """
    search_key = get_search_key(request)
    
    if search_key is None:
        return _get_default_search_vars()
    
    user_data = retrieve_cache_search_key(search_key)
    if user_data is None:
        user_data = _get_history_vars(request, search_key)
    
    # check data validity
    user_data = get_form_filters(user_data)
    defaults = _get_default_search_vars()
    
    for key in defaults:
        if not key in user_data:
            user_data[key] = defaults[key]
    
    # clean the data keys
    user_data = clean_search_key_dates(user_data)
    user_data = clean_geo_keys(user_data)
    
    return user_data
    

def _get_search_cookie_vars(request):
    """
    get's search data associated with the request cookie skey
    """
    search_key = request.COOKIES.get(SEARCH_KEY_COOKIE_NAME, None)
    
    if search_key != None:
        search_filters = _get_history_vars(request, search_key)
    else:
        search_filters = _get_default_search_vars()
    
    return search_filters


def _get_history_vars(request, search_key):
    """
    retreives search key data from noSQL
    if not exists, returns a default search data dict
    """
    if search_key != None:
        # key does not exists locally
        # so we try to get it from dynamodb repository
        try:
            history_data = _history_connector.get_latest(search_key)
            assign_cache_search_key( search_key, history_data )
        except:
            history_data = _get_default_search_vars()
            logger.warn( 'Unable to retreive key '+search_key )
        
        # key does not exists in repository
        if history_data != None:
            search_filters = history_data
        else:
            # so it's a mishandled key ... consider as new user
            search_filters = _get_default_search_vars()
    else:
        search_filters = _get_default_search_vars()
    
    return search_filters

def set_halfed_hours(date_time):
    """
    set halfed hours on a datetime
    """
    if date_time.minute > 30:
        date_time = date_time.replace(minute=0)
        date_time = date_time + timedelta(hours=1)
    elif date_time.minute == 0:
        pass
    else:
        date_time = date_time.replace(minute=30)
    
    return date_time

def save_search_session_vars(request, data):
    """
    saves data to search session data associated with the request
    """
    user_data = {}
    
    # apply filtering
    post_data = get_form_filters(data)
    for key in post_data:
        user_data[key] = post_data[key]
    
    # save search_key
    session_key = request.session.session_key
    search_key = save_search_key(request, session_key, user_data)
    
    return user_data, search_key
    
    
def update_search_session_vars(request, data=None):
    """
    updates search session data with the data if provided 
    or the current search session vars
    then saves it
    """
    #
    if data == None:
        search_filters = get_search_session_vars(request)
    else:
        search_filters = data
    
    search_filters = update_from_request(request, search_filters)
    
    # save search_key
    session_key = request.session.session_key
    search_key = save_search_key(request, session_key, search_filters)
    
    return search_filters, search_key


def clean_search_key_dates(input_data):
    """
    parses and replaces search data start/end dates if not valid
    dates are always provided as naive, 
    and related to the user context, so concidered as local
    in the current language and current timezone
    TODO
    save timezone within the search key data
    """
    current_language = translation.get_language()
    current_timezone = timezone.get_current_timezone()
    current_now = timezone.localtime(timezone.now())
    
    if current_language == 'en':
        date_format = "%m/%d/%Y"
    else:
        date_format = "%d/%m/%Y"
    
    # validate the dates (start/end as DD/MM/YYYY HH:MM)
    
    # start be valid date time object
    #     -> false resets the time object
    try:
        start = datetime.strptime(input_data['start_date'] + ' ' + input_data['start_hour'], date_format + " %H:%M")
        # localize to the current timezone
        start = current_timezone.localize(start)
    except:
        start = get_rounded_time(current_now + timedelta(hours=2))


    # start after now + 1h
    #     -> false resets start date
    if start < current_now + timedelta(hours=1):  # no utc
        start = get_rounded_time(current_now + timedelta(hours=2))
    
    # end be valid date time object
    #     -> false resets end date
    try:
        end = datetime.strptime(input_data['end_date'] + ' ' + input_data['end_hour'], date_format + " %H:%M")
        # localize to the current timezone
        end = current_timezone.localize(end)
    except:
        end = start+timedelta(days=1)


    # with end after start+1h
    #     -> false resets the end date
    if end < start+timedelta(hours=1):
        end = start + timedelta(days=1)
    
    # with a duration not exceeding 6 month
    #     -> false resets the end date
    if end > start+timedelta(days=6*30):
        end = start + timedelta(days=1)
    
    
    input_data['start_date'] = start.strftime(date_format)
    input_data['start_hour'] = start.strftime("%H:%M")
    input_data['end_date'] = end.strftime(date_format)
    input_data['end_hour'] = end.strftime("%H:%M")
        
    return input_data


def clean_geo_keys(input_data):
    """
    parse and validates search lat/lng are floats 
    and search radius is integer
    """
    try:
        float(input_data['search_lat'])
        float(input_data['search_lng'])
    except:
        input_data['search_lat'] = ''
        input_data['search_lng'] = ''
    
    try:
        int(input_data['search_radius'])
    except:
        input_data['search_radius'] = ''
    
    return input_data


def update_from_request(request, data):
    """
    updates dict data with request POST, then GET data
    """
    incoming_data = data
    
    # override old search params
    if 'full_address' in incoming_data:
        incoming_data['search_input'] = incoming_data['full_address']
        incoming_data['search_lat'] = ''
        incoming_data['search_lng'] = ''
        incoming_data['search_radius'] = ''
    
    if 'start_time' in incoming_data:
        try:
            start = set_halfed_hours( datetimetz_from_string( incoming_data['start_time'] ) )
            current_language = translation.get_language()
            if current_language == 'en':
                incoming_data['start_date'] = start.strftime("%m/%d/%Y")
            else:
                incoming_data['start_date'] = start.strftime("%d/%m/%Y")
            
            incoming_data['start_hour'] = start.strftime("%H:%M")
        except:
            pass
    
    if 'end_time' in incoming_data:
        try:
            end = set_halfed_hours( datetimetz_from_string( incoming_data['end_time'] ) )
            current_language = translation.get_language()
            if current_language == 'en':
                incoming_data['end_date'] = end.strftime("%m/%d/%Y")
            else:
                incoming_data['end_date'] = end.strftime("%d/%m/%Y")
            incoming_data['end_hour'] = end.strftime("%H:%M")
        except:
            pass
    
    # override any parameter with the posted one
    for key in request.POST:
        incoming_data[key] = request.POST[key]
    
    # gether the get params, they have the word as part of the url ...
    for key in request.GET:
        incoming_data[key] = request.GET[key]
    
    # finally filter to conform filter forms
    post_data = get_form_filters(incoming_data)
    for key in post_data:
        data[key] = post_data[key]
    
    return data


def set_search_cookie_vars(request, response):
    """
    set's the response search key cookie
    """
    search_key = get_search_key(request)

    if search_key is not None:
        response.set_cookie(SEARCH_KEY_COOKIE_NAME, search_key)

