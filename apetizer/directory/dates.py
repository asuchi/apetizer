'''
Date related utilities

Created on Oct 3, 2011

@author: greg
'''
#from dateutil.relativedelta import relativedelta

import datetime

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.conf.global_settings import DATETIME_INPUT_FORMATS
from django.core.exceptions import ValidationError
from django.forms.fields import DateTimeField
from django.utils import timezone
from django.utils.formats import get_format
from django.utils.timezone import now
from django.utils.translation import ugettext as _
import pytz


def round_duration_to_half_hour(td):
    '''
    Given a timedelta, round it to the nearest 30 minutes
    '''
    td += datetime.timedelta(seconds=900)
    td -= datetime.timedelta(seconds=td.seconds % 1800,
                             microseconds=td.microseconds)
    return td


def duration_minutes(start_time, end_time):
    '''
    Given a start and end datetime, return the whole number of minutes 
    this time period encompasses.
    '''
    duration = end_time - start_time
    return (duration.days * 1440) + (duration.seconds // 60)


def format_duration(start_or_td, end=None, format_type='abbrev'):
    ''' 
    Given a start and end datetime or a timedelta, return a human readable 
    formatted string describing the duration.  Uses current language for l10n.
    
    Pass an optional format_type to control output.  Choices are 'long', 'abbrev', 
    and 'compact'.
    '''
    if isinstance(start_or_td, datetime.timedelta):
        return format_timedelta(start_or_td, format_type=format_type)
    elif not end:
        raise ValueError("Must provide a start and end date(time) if not using timedelta")
    
    return _format_duration(relativedelta(end, start_or_td), format_type=format_type)


def format_timedelta(td, format_type='abbrev'):
    ''' 
    Given a timedelta, return a human readable formatted string
    describing the duration.  Uses current language for l10n.
    
    Pass an optional format_type to control output.  Choices are 'long', 'abbrev', 
    and 'compact'.
    '''
    return _format_duration(relativedelta(seconds=int(td.total_seconds())), format_type=format_type)


def _format_duration(rd, format_type='abbrev'):
    ''' 
    Given a relativedelta, return a human readable formatted string
    describing the duration.  Uses current language for l10n.
    
    Pass an optional format_type to control output.  Choices are 'long', 'abbrev', 
    and 'compact'.
    '''
    # time units we are interested in descending order of significance
    tm_long_units = (
        ('years', _(u' year'), _(u' years')), 
        ('months', _(u' month'), _(u' months')), 
        ('days', _(u' day'), _(u' days')),
        ('hours', _(u' hour'), _(u' hours')), 
        ('minutes', _(u' minute'), _(u' minutes')), 
        ('seconds', _(u' second'), _(u' seconds')),
    )

    tm_abbrev_units = (
        ('years', _(u' yr'), _(u' yrs')), 
        ('months', _(u' mo'), _(u' mos')), 
        ('days', _(u'  day'), _(u'  days')),
        ('hours', _(u' hr'), _(u' hrs')), 
        ('minutes', _(u' min'), _(u' mins')), 
        ('seconds', _(u' sec'), _(u' secs')),
    )

    tm_compact_units = (
        ('years', _(u'y'), _(u'y')), 
        ('months', _(u'm'), _(u'm')), 
        ('days', _(u'd'), _(u'd')),
        ('hours', _(u'h'), _(u'h')), 
        ('minutes', _(u'm'), _(u'm')), 
        ('seconds', _(u's'), _(u's')),
    )
    
    if format_type == 'compact':
        tm_units = tm_compact_units
    elif format_type == 'abbrev':
        tm_units = tm_abbrev_units
    else:
        tm_units = tm_long_units

    formatted_units = []
    for idx, tm_unit in enumerate(tm_units): #@UnusedVariable
        unit_val = getattr(rd, tm_unit[0])
        if unit_val > 0:
            unit = '%2d%s' % (unit_val, tm_unit[1] if unit_val == 1 else tm_unit[2])
            formatted_units.append(unit)

    if not formatted_units:
        return ''
    
    joinstr = ', '
    if format_type in ('compact', 'abbrev'):
        joinstr = ' '

    return joinstr.join(formatted_units)


def ceil_to_quarter_hour(dt):
    '''
    Advances a datetime to the nearest quarter hour.
    '''
    minutes_to_add = 15 - (dt.minute % 15)
    rdt = dt.replace(second=0, microsecond=0) + relativedelta(minutes=minutes_to_add)
    return rdt


def floor_to_quarter_hour(dt):
    '''
    Advances a datetime to the nearest quarter hour.
    '''
    minutes_to_substract = dt.minute % 15
    rdt = dt.replace(second=0, microsecond=0) + relativedelta(minutes=-minutes_to_substract)
    return rdt


def next_quarter_hour():
    '''
    Return the next quarter hour (in UTC).
    '''
    n = ceil_to_quarter_hour(now())
    return n


def datetimetz_from_string(dtstr, add_days=1):
    '''
    Given a string, parse it using the buzzcar standard (for the locale) and return the
    python datetime it represents.  If that fails choose a default time, adding add_days
    days to it.  This method is timezone AWARE - it will return the resulting datetime in
    the timezone returned by global_tz.get_timezone().
    '''
    #dt_formats = [get_format('DATETIME_INPUT_FORMAT_NO_SECONDS')] + list(DATETIME_INPUT_FORMATS)
    dt_formats = list(DATETIME_INPUT_FORMATS)
    dt = None
    
    if dtstr:
        try:
            dt = DateTimeField(input_formats=dt_formats).to_python(dtstr)
            if dt.tzinfo is None:
                dt = timezone.get_current_timezone().localize(dt)
        except ValidationError:
            pass
        
    if not dt:
        dt = (next_quarter_hour() + datetime.timedelta(days=add_days)).astimezone(timezone.get_current_timezone())

    return dt




def start_datetimetz_from_string(datetimestr):
    return datetimetz_from_string(datetimestr, 1)


def end_datetimetz_from_string(datetimestr):
    return datetimetz_from_string(datetimestr, 2)



def shift_to_local_time(utc_datetime, local_timezone=None):
    '''
    Convert to local time for display purposes
    '''
    if not local_timezone:
        local_timezone = timezone.get_default_timezone()

    if utc_datetime:
        return local_timezone.normalize(utc_datetime)
    return None


def shift_to_db_time(local_datetime):
    '''
    Convert from local time for saving to the database
    '''
    if local_datetime:
        return pytz.utc.normalize(local_datetime.astimezone(pytz.utc))
    return None

def datetime_from_how(start_dt, how, inclusive=True):
    '''
    Given a starting datetime (or date, in which case midnight is assumed) and hour of 
    the week, return the datetime it represents.

    If not inclusive, returns the hour prior. 
    '''
    if isinstance(start_dt, datetime.datetime):
        new_dt = start_dt
    else:
        new_dt = datetime.datetime.combine(start_dt, datetime.time(tzinfo=pytz.timezone(settings.TIME_ZONE)))
    if not inclusive and new_dt.minute == 0:
        new_dt = new_dt - datetime.timedelta(hours=1) 
    return new_dt + datetime.timedelta(hours=how)

def how_from_datetime(dt, inclusive=True):
    '''
    Given a datetime (or date, in which case midnight is assumed), return the 
    hour of the week it represents, 0 <= how <= 167.
    
    If not inclusive and the datetime has no minutes, returns the hour prior. 
    '''
    if isinstance(dt, datetime.datetime):
        new_dt = dt
    else:
        new_dt = datetime.datetime.combine(dt, datetime.time(tzinfo=pytz.timezone(settings.TIME_ZONE)))
    if not inclusive and new_dt.minute == 0:
        new_dt = new_dt - datetime.timedelta(hours=1) 
    return (new_dt.weekday() * 24) + new_dt.hour

def datetimes_to_how_range(start_datetime, end_datetime, wrap=True):
    '''
    Given two datetimes, return the range of hours of a week their interval encompasses, 
    given the ISO standard of midnight Monday == 0 according to UTC timezone.
    
    The range is start and end inclusive, for compatibility with Django's range filter.
    
    If wrap is True (the default):
        If they are more than a week apart a week of hours (0 -> 167) is returned.  
    
        The start hour of the week may be greater than the end hour, which could 
        happen if (say) the start_datetime is on a Sunday and the end_datetime on a 
        Monday.
    '''

    end_datetime = end_datetime.astimezone(start_datetime.tzinfo)

    if end_datetime <= start_datetime:
        raise ValueError('end datetime must fall after start')

    s_how = how_from_datetime(start_datetime, inclusive=True)
    e_how = how_from_datetime(end_datetime, inclusive=False)
    
    duration = end_datetime - start_datetime
    if duration >= datetime.timedelta(days=7) and wrap:
        return (0, 167)

    if not wrap:
        # Handle wrapping by extending end how as far as needed
        addl_weeks = max(0, (duration.days / 7) - 1)
        if e_how < s_how:
            addl_weeks = addl_weeks + 1
        e_how = e_how + (168 * addl_weeks)

    return (s_how, e_how)


