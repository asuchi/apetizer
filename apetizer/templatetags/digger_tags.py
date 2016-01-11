'''
Created on 17 mai 2015

@author: rux
'''
from django import template

from apetizer.utils.digger import extract_dates as extractor

register = template.Library()

@register.simple_tag(takes_context=True)
def extract_dates( context, string ):
    
    #print string
    dates = extractor(string)
    
    rs = '<label>DATES:</label>'
    #if len(dates):
    #    print string
    for date in dates:
        print date
        rs += ''+str(date)+''
    
    return rs

