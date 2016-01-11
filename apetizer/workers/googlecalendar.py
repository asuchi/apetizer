'''
Created on 30 sept. 2015

@author: biodigitals
'''
import requests

from apetizer.models import Item
from apetizer.workers.base import BaseWorker


class GoogleCalendarDigger(BaseWorker):
    
    calendar_id = 'cf01la1ejk30973ac2fd0qfgng@group.calendar.google.com'
    
    def request(self, **kwargs):
        
        self.calendar_id = 'payetonplan@gmail.com'
        
        #calendar_url = 'http://www.google.com/calendar/feeds/'+self.calendar_id+'/public/full?orderby=starttime&sortorder=ascending&futureevents=true&alt=json'
        
        calendar_url = 'https://www.googleapis.com/calendar/v3/calendars/'+self.calendar_id+'/events?userIp=88.140.248.245&key=AIzaSyAuSt4Yu-DRLbvr-bUxkB7yb_H0ldq-Hxw'
        
        r = requests.get(calendar_url)
        
        data = r.json()
        
        #print data
        
        return data
    
    def parse(self, **kwargs):
        data = self.raw_data
        keyword = self.input_data.get('keyword')
        
        for status in data['items']:
            
            id = status.get('id')
            link = status.get('htmlLink', id)
            name = status.get('name', id)
            title = status.get('summary', name)
            description = status.get('description', title)
            
            #extract_dates(description)
            
            item = Item()
            
            item.label = name
            
            item.related_link = link
            item.slug = id
            item.username = name
            item.label = keyword
            item.title = status.get('summary')
            item.description = description
            
            self.items.append(item)
        return self.items
