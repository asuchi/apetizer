'''
Created on 30 sept. 2015

@author: biodigitals
'''
import datetime
import json
from os.path import os
from pprint import pprint

from dateutil import parser
from django.core.exceptions import ObjectDoesNotExist
from django.utils.datetime_safe import strftime
import requests

from apetizer.models import Item
from apetizer.workers.base import BaseWorker


# https://secure.meetup.com/meetup_api/console/
class MeetupWorker(BaseWorker):
    
    meetup_api_key = '5971545d4317bf6936521750624c49'

    def request(self, **kwargs):
        self.items = []
        related_url = self.node.related_url
        if self.node.related_url[-1] == '/':
            related_url = related_url[:-1]
        
        self.keyword = os.path.split(related_url)[1]
        if not self.keyword:return []
        
        #meetup_url = 'https://api.meetup.com/legitenumerique?photo-host=public&page=20&sig_id=186265380&sig=1c8ca3cabe7181a82ffcc06f6c388016ad6714d6'
        #meetup_url = 'https://api.meetup.com/legitenumerique?key='+self.meetup_api_key
        
        #https://api.meetup.com/2/events?&sign=true&photo-host=public&group_urlname=
        
        meetup_url = 'https://api.meetup.com/2/events/?group_urlname='+self.keyword+'&key='+self.meetup_api_key
        
        r = requests.get(meetup_url)
        data = r.json()
        self.raw_data = data
        #print data
        return data
    
    def parse(self, **kwargs):
        for status in self.raw_data['results']:
            self.items.append(self.get_item(status))
        return self.items
        
    def get_item(self, data):
        
        sid = data.get('id')
        
        item = Item.objects.get_or_create_url(self.node.get_path()+'/'+sid, **self.kwargs)
        
        item.label = data['group']['name']
        item.title = data.get('name', sid)
        item.description = data.get('title', 'Meetup')
        item.content = data.get('description', '')
        
        item.latitude = data['venue'].get('lat')
        item.longitude = data['venue'].get('lon')
        
        item.data = json.dumps(data)
        item.geojson = json.dumps({'Features':[{"Properties":data['venue']}]})
        
        
        pprint(data)
        
        item.start = datetime.datetime.fromtimestamp(
                        (data['time']/1000)
                    )#.strftime('%Y-%m-%d %H:%M:%S')
        
        item.end = datetime.datetime.fromtimestamp(
                        (data['time']/1000)
                    )#.strftime('%Y-%m-%d %H:%M:%S')
        
        item.related_url = data.get('event_url', sid)
        
        item.full_clean()
        item.save()
        
        return item

