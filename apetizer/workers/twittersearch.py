'''
Created on 16 oct. 2015

@author: biodigitals
'''
from django.conf import settings
import twitter

from apetizer.models import Item, get_new_uuid
from apetizer.workers.base import BaseWorker


class TwitterWorker(BaseWorker):
    
    def request(self, **kwargs):
        """
        Gether the needed data
        """
        keyword = self.input_data.get('keyword')
        
        # twitter urls are like
        # https://twitter.com/hashtag/jinsiste?src=hash
        # https://twitter.com/quelqun/
        
        
        # class the api
        api = twitter.Api(consumer_key=settings.TWITTER_CONSUMER_KEY,
                          consumer_secret=settings.TWITTER_CONSUMER_SECRET,
                          access_token_key=settings.TWITTER_ACCESS_TOKEN_KEY,
                          access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET,)
        
        self.raw_data = api.GetSearch(keyword)

    def parse(self, **kwargs):
        """
        Parse obtained data dict
        """
        items = []
        for status in self.raw_data:
            try:
                item = Item.objects.filter(slug=status.id, parent=self.node).order_by('-ref_time')[0]
            except:
                item = Item()
                itrans = item.get_translation()
                item.pk = item.id = get_new_uuid()
                item.parent = self.node
                
                itrans.slug = str(status.id)
            
                item.username = '@'+status.user.name
                item.email = ''
                item.status = 'imported'
                item.locale = 'fr'
                #item.akey = ge
                
                item.path = self.node.related_url
                item.action = 'related'
                
                item.label = self.input_data['keyword']
                itrans.title = status.text
                #item.related_id = item.id
                if self.input_data.get('save'):
                    item.save()
                
                print item.pk
            items.append(item)
        self.items = item
        return items
