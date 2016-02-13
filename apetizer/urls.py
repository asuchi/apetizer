'''
Created on 15 janv. 2013

@author: rux
'''

from django.conf import settings
from django.conf.urls import patterns, url, include
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from apetizer.sitemap import ContentSitemap
from apetizer.views.front import FrontView

admin.autodiscover()

handler404 = 'apetizer.views.front.handler404'
handler500 = 'apetizer.views.front.handler500'

urlpatterns = patterns( '', 
        
        url(r'^sitemap\.xml$', sitemap, {'sitemaps':{'content': ContentSitemap()}},
            name='django.contrib.sitemaps.views.sitemap'),
        
        # homepage
        url(r'^$',
            FrontView.as_view(),
            name='home',
            kwargs={'action':FrontView.default_action}),
        
        url(FrontView.get_url_regexp(r'^')+'\/$',
            FrontView.as_view(),
            kwargs={'path':'/'}),
        
        url(FrontView.get_url_regexp(r'^(?P<path>.+)\/'),
            FrontView.as_view(),
            name=FrontView.view_name,),
        
        url(r'^(?P<path>.+)\/$',
            FrontView.as_view(),
            name='home',
            kwargs={'action':FrontView.default_action}),
        
                       
        )

# This is only needed when using runserver.
if settings.DEBUG or True:
    urlpatterns = patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve',  # NOQA
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
        ) + staticfiles_urlpatterns() + urlpatterns  # NOQA

