'''
Created on 19 janv. 2014

@author: rux
'''
from django.contrib.sitemaps import Sitemap
from apetizer.models import Item


class ContentSitemap(Sitemap):
    
    changefreq = "never"
    priority = 0.5
    
    def items(self):
        return Item.objects.filter(published=True)

    def location(self, item):
        return item.get_url()
    
    def lastmod(self, item):
        return item.modified_date
    
    def change_freq(self, item):
        return 'weekly'
        return 'monthly'
