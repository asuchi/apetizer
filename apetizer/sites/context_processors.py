from django.conf import settings
from django.contrib.sites.models import Site

from apetizer.models import Frontend


def current_site(request):
    return (settings.SITE_ID) and {'site': Site.objects.get_current()} or {}
