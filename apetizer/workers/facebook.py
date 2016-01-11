'''
Created on 30 sept. 2015

@author: biodigitals
'''
from django.utils.timezone import now
import requests

from apetizer.models import Item
from apetizer.workers.base import BaseWorker


# http://fr.slideshare.net/stemmark/diy-basic-facebook-data-mining
# https://developers.facebook.com/tools/explorer/
class FacebookGroupView(BaseWorker):

    def request(self, **kwargs):
        
        keyword = self.input_data.get('keyword')
        
        # get the group id from keyword
        graph_url = 'https://graph.facebook.com/search?q='+keyword+'&type=group&access_token='+self.token
        r = requests.get(graph_url)
        if not len(r.json()['data']):
            return {}
        group_id = r.json()['data'][0]['id']
        
        # get the group feed
        graph_url = 'https://graph.facebook.com/'+group_id+'/feed?access_token='+self.token
        r = requests.get(graph_url)
        
        data = r.json()['data']
        
        self.raw_data = data
    
    def parse(self, **kwargs):
        
        token = 'CAACEdEose0cBAPemNCRC53fdEpBFWzVyCDBHWunsePzgZAW6U7xZAflPwmWW1GMixFpDSyhOLKdUR9GAV2BA3qqWdFBL2UoQDDRsvqFQ9n6sC1izct94BkKfakJZBrODfFB0NdZAxNrUyolxeojnWN829rvcX4gyLpkZBwcQJdnxeBBPpcZC4ojO1l00ZAbFESDx0vlcZCGSuzAHxPe13QfL'
        keyword = self.input_data.get('keyword')
        
        for status in self.raw_data:
            
            type = status.get('type')
            
            if type == 'event':
                event_id = status.get('object_id')
            elif type == 'status':
                event_id = status.get('id').split('_')[1]
            else:
                event_id = None
            
            # skip non event stuff
            if event_id:
                
                # get the event data
                graph_url = 'https://graph.facebook.com/'+event_id+'?access_token='+self.token
                r = requests.get(graph_url)
                event_data = r.json()
                
                # text
                label = status.get('name', id)
                title = event_data.get('name', id)
                
                description = event_data.get('description', title)
                content = ''

                link = status.get('link', id)
                
                # time
                timezone = event_data.get('timezone')
                start = event_data.get('start_time')
                end = event_data.get('end_time', start)
                
                # location
                location = event_data.get('location')
                event_venue = event_data.get('venue',{})
                
                address = ', '.join((event_venue.get('street', ''),
                                     event_venue.get('zip', ''),
                                     event_venue.get('city', ''),
                                     event_venue.get('country', ''),))
                
                latitude = event_venue.get('latitude', None)
                longitude = event_venue.get('longitude', None)
                
                #
                picture = status.get('link', id)
            else:
                print status
                    
                # text
                link = status.get('link', None)
                label = status.get('name', id)
                title = status.get('name', id)
                description = status.get('message', title)
                
                start = end = now()
                
                location = ''
                address = ''
                latitude = None
                longitude = None
             
            #
            if description:
                item = Item()
                item.slug = id
                item.related_url = link
                
                item.start = start
                item.end = end
                
                item.location = location
                item.address = address
                
                item.latitude = latitude
                item.longitude = longitude
                
                item.slug = id
                item.label = keyword
                item.title = title
                item.description = description
                item.content = content
                
                item.parent = self.node
                
                self.items.append(item)
        
            return self.items
        