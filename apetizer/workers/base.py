'''
Created on 16 oct. 2015

@author: biodigitals
'''
from django.conf import settings
from apetizer.models import Item, get_new_uuid


# https://github.com/nderkach/couchsurfing-python
# https://github.com/nderkach/airbnb-python
# ...
# http://navitia.io/
# https://github.com/goldsmith/Wikipedia
# le bon coin ?
# http://www.magazine-avantages.fr/,6-sites-100-recup-et-troc,2300116,7570.asp
# http://bonplangratos.fr/recup
# meetup api ?
# openstreetmap !!!
# https://data.sncf.com/
# ideas ... https://flatturtle.com/

class BaseWorker(object):
    raw_data = ''
    data = {}
    items = []
    def __init__(self, user_profile, node, input_data, kpipe, **kwargs):
        self.user_profile = user_profile
        self.node = node
        self.input_data = input_data
        self.kwargs = kpipe
        return super(BaseWorker, self).__init__(**kwargs)
    
    def prepare(self, **kwargs):
        """
        Prepare the job
        """
        # get the data from the source
        #self.node.is_busy = True
        #self.node.save()
        
        self.request()
        # work with the data to prepare a list of node to insert
        self.parse()
        
        # save the node list
        self.persist()
        
        # write moderation telling the job is finished
        #self.node.is_busy = False
        #self.node.save()
        
        return self.items
        

    def request(self, **kwargs):
        """
        Gether the needed data
        """
        self.raw_data = '[]'
        

    def parse(self, **kwargs):
        """
        Parse obtained data dict
        """
        for status in self.raw_data:
            try:
                item = Item.objects.filter(slug=status.id, parent=self.node).order_by('-ref_time')[0]
            except:
                item = Item()
                item.pk = item.id = get_new_uuid()
                item.parent = self.node
                
                item.slug = str(status.id)
                item.label = 'Message'
                item.title = status.text
                
                item.username = '@'+status.user.name
                item.email = ''
                item.status = 'imported'
                item.locale = 'fr'
                item.akey = self.user_profile.akey
                item.path = self.node.related_url
                item.action = 'related'
                
                #item.save()
                
            self.items.append(item)
        
        return self.items

    def persist(self, ids=None):
        """
        Push ids data to the database
        """
        if not self.input_data.get('save'):
            return
        
        if ids == None:
            for item in self.items:
                item.save()
        else:
            for item in self.items:
                if item.id in ids:
                    item.save()



