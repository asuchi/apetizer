from django.conf import settings
from django.conf.urls import patterns, url, include
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

admin.autodiscover()

handler404 = 'apetizer.views.front.handler404'
handler500 = 'apetizer.views.front.handler500'

urlpatterns = patterns('',
     url(r'^admin/', include(admin.site.urls)),
     url(r'^', include('apetizer.urls')),
)

# This is only needed when using runserver.
if settings.DEBUG or True:
    urlpatterns = patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve',  # NOQA
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
        ) + staticfiles_urlpatterns() + urlpatterns  # NOQA