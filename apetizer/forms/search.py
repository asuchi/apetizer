'''
Forms for explore app

Created on Oct 7, 2013

@author: rux
'''
import logging

from django import forms
from django.forms.widgets import Select, HiddenInput, DateInput
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

from apetizer.utils.compatibility import unicode3


logger = logging.getLogger(__name__)

def get_types_choices():
    return {}


class DirectoryQueryForm(forms.Form):
    '''
    Main search input handling the raw search input
    I actually handles only the search term
    '''
    query = forms.CharField(label=_(u'What ?'), max_length=16, min_length=3)
    
    def __init__(self, *args, **kwargs):
        super(SearchKeywordForm, self).__init__(*args, **kwargs)

class SearchInputForm(forms.Form):
    '''
    Main search input handling the raw search input
    I actually handles only the search term
    '''
    title = 'Search'
    search_input = forms.CharField(label=_(u'Where ?'))
    
    def __init__(self, *args, **kwargs):
        '''
        Need to make the formats dynamic as they vary per request
        '''
        super(SearchInputForm, self).__init__(*args, **kwargs)

class SearchKeywordForm(forms.Form):
    '''
    Main search input handling the raw search input
    I actually handles only the search term
    '''
    title = 'Search'
    search_keyword = forms.CharField(label=_(u'What ?'))
    
    def __init__(self, *args, **kwargs):
        super(SearchKeywordForm, self).__init__(*args, **kwargs)


def get_hour_ranges():
    
    hour_ranges = []
    
    for h in range(24):
        for m in range(2):
            if int(h) == 0:
                h = '00'
            elif int(h) < 10:
                h = '0'+str(h)
            if int(m) == 0:
                m = '00'
                tstring = str(h)+':'+str(m)
            else:
                tstring = str(h)+':'+str(m*30)
            
            hour_ranges.append( (tstring,tstring) )
    
    return hour_ranges


class UserInputForm(forms.Form):
    '''
    User parameters for reservation
    '''
    hour_ranges = get_hour_ranges()
    
    current_language = translation.get_language()
    
    if current_language == 'en':
        date_format = '%m/%d/%Y'
    else:
        date_format = '%d/%m/%Y'
    
    start_date = forms.DateField(label=_(u'Starts'),widget=DateInput(format=date_format))
    start_hour = forms.CharField(label=_(u"Hour"),widget=Select(choices=hour_ranges) )
    
    end_date = forms.DateField(label=_(u'Ends'))
    end_hour = forms.CharField(label=_(u"Hour"),widget=Select(choices=hour_ranges) )
    
    def __init__(self, *args, **kwargs):
        '''
        Need to make the formats dynamic as they vary per request
        '''
        super(UserInputForm, self).__init__(*args, **kwargs)



class SearchSettingsForm(forms.Form):
    '''
    Hidden search settings for search location
    '''
    title = _('Search radius')
    slug = 'search-radius-filter'
    
    search_lat = forms.CharField(label=_(u'Search lat'),widget=HiddenInput())
    search_lng = forms.CharField(label=_(u'Search long'),widget=HiddenInput())
    
    search_radius = forms.IntegerField(label=_(u'Search radius'),widget=HiddenInput())
    
    search_town = forms.CharField(label=_(u'Search town'),widget=HiddenInput())
    search_l1 = forms.CharField(label=_(u'Search administrative_area_1'),widget=HiddenInput())
    search_l2 = forms.CharField(label=_(u'Search administrative_area_2'),widget=HiddenInput())
    
    search_path = forms.CharField(label=_(u'Search directory path'),widget=HiddenInput())
    #search_tab = forms.CharField(label=_(u'Search tab display'),widget=HiddenInput())

class SearchTypesForm(forms.Form):
    '''
    Dynamic form to manage vehicle types filtering
    '''
    title = _('Vehicle type')
    slug = 'search-types-filter'
    
    def __init__(self, *args, **kwargs):
        '''
        Need to make the formats dynamic as they vary per request
        '''
        super(SearchTypesForm, self).__init__(*args, **kwargs)
        for itype in get_types_choices():
            self.fields['type_'+itype[0]] = forms.BooleanField( initial=False, label=_(itype[1]) )


MAX_AGES = (
        (0,_('All years')),
        (1,_('One year')),
        (2,_('Two years')),
        (3,_('Three years')),
        (4,_('Four years')),
        (5,_('Five years')),
)

class SearchAgeForm(forms.Form):
    '''
    Age search filter form
    '''
    title = _('Age')
    slug = 'search-age-filter'
    #
    max_age = forms.IntegerField(label=_(u'Maximum age'),initial=0,widget=Select(choices=MAX_AGES, attrs={'class': 'auto-width'}))
    
    def __init__(self, *args, **kwargs):
        '''
        Need to make the formats dynamic as they vary per request
        '''
        super(SearchAgeForm, self).__init__(*args, **kwargs)




class SearchPageForm(forms.Form):
    '''
    Hidden form top handle search result paging
    '''
    page = forms.IntegerField(label=_(u'Search result page'),widget=HiddenInput())
    #search_offset = forms.IntegerField(label=_(u'Search result offset'),widget=HiddenInput())
    #search_limit = forms.IntegerField(label=_(u'Search result limit'),widget=HiddenInput())


SORT_OPTIONS = ('cheapest', 'most_expensive', 'closest', 'newest')

DISPLAY_SORT_CHOICES = (
    ("", _("Ranking")),
    ("cheapest", _("Cheapest")),
    ("most_expensive", _("Most expensive")),
    ("closest", _("Closest")),
    ("newest", _("Newest")),
)


class SearchSortForm(forms.Form):
    '''
    Form top handle search result sorting
    '''
    search_sort_by = forms.CharField(label=_(u'Sort by'), widget=Select(choices=DISPLAY_SORT_CHOICES))
    search_display_unvisible = forms.BooleanField(label=_(u'Show unvisible articles'))


# BELLOW TO REFACTOR

class NameModelChoiceField(forms.ModelChoiceField):
    '''
    Custom ModelChoiceField to use obj.name instead of unicode, which modeltranslation
    had trouble with.
    '''
    def label_from_instance(self, obj):
        return getattr(obj, "name", unicode3(obj))


