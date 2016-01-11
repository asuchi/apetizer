'''
Created on 6 juil. 2015

@author: rux
'''
from datetime import datetime
import re
from time import mktime
import unicodedata

#http://iamtrask.github.io/2015/07/12/basic-python-network/


def timestamp_to_datetime(timestamp):
    """
    Converts string timestamp to datetime
    with json fix
    """
    if isinstance(timestamp, (str, unicode)):

        if len(timestamp) == 13:
            timestamp = int(timestamp) / 1000

        return datetime.fromtimestamp(timestamp)
    else:
        return ""


def datetime_to_timestamp(date):
    """
    Converts datetime to timestamp
    with json fix
    """
    if isinstance(date, datetime):

        timestamp = mktime(date.timetuple())
        json_timestamp = int(timestamp) * 1000

        return '{0}'.format(json_timestamp)
    else:
        return ""


def strip_accents(s):
    try:
        return ''.join(c for c in unicodedata.normalize('NFD', s)
                           if unicodedata.category(c) != 'Mn')
    except:
        print 'NOT UNICODE'
        print s


def extract_dates(message):
    
    
    message = strip_accents(message.lower())
    
    if message is None:
        return []
    
    dates = []
    
    start_pattern = '(\s|,|;|\.|\||-|\/|^)+'
    end_pattern = '(\s|,|;|\.|\||-|\/|$)+'
    
    enum_pattern = '(\s|,|,\s|\.)'
    space_pattern = '(\s|\.)'
    
    week_day_regexp = '(?P<weekday>((lun(di|\.)?)|(mar(di|\.)?)|(merc(redi|\.)?)|(jeu(di|\.)?)|(ven(dredi|\.)?)|(sam(edi|\.)?)|(dim(anche|\.)?))+)?'
    
    day_num_regexp = '(?P<daynum>0[1-9]|[1-9]|1[0-9]|2[0-9]|3[0-1]|premier|1er)'
    
    #months = [strip_accents(unicode(datetime.date(2000, m, 1).strftime('%B').lower())) for m in range(1, 13)]
    month_regexp = '(?P<month>'
    
    months = ('janvier','fevrier','mars','avril','mai','juin','juillet','aout','septembre','octobre','novembre','decembre')
    
    for month in months:
        month_regexp += '('+month[:3]+'('+month[3:]+'|\.)?)|'
    
    month_regexp += '(0[1-9]|[1-9]|1[0-2])'
    month_regexp += ')'
    
    date_regexp = week_day_regexp+enum_pattern+day_num_regexp+space_pattern+month_regexp+'+'+end_pattern
    
    result = re.finditer(date_regexp, message)
    for match in result:
        dates.append(match.groupdict())

    return dates

