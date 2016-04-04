'''
Created on 15 janv. 2013

@author: rux
'''
from django.conf.urls import patterns, url
from apetizer.views.directory import DirectoryView
from apetizer.views.front import FrontView

handler404 = 'apetizer.views.front.handler404'
handler500 = 'apetizer.views.front.handler500'

urlpatterns = patterns( '', 
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
        
        # directory views
        url(r'^(?P<path>.+)\/directory/$',
            DirectoryView.as_view(),
            name=DirectoryView.view_name,
            kwargs={'action':DirectoryView.default_action}),
        
        url(r'^(?P<path>.+)\/query.json$',
            DirectoryView.as_view(),
            name=DirectoryView.view_name,
            kwargs={'action':'query'}),
        )
