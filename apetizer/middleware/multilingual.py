# -*- coding: utf-8 -*-
import logging
import re

from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils import translation

from apetizer.utils.compatibility import unicode3


logger = logging.getLogger(__name__)


URLS_WITHOUT_LANGUAGE_REDIRECT = getattr(settings, 'URLS_WITHOUT_LANGUAGE_REDIRECT', ())

def get_default_language(language_code=None):
    """Returns default language depending on settings.LANGUAGE_CODE merged with
    best match from settings.LANGUAGES
    Returns: language_code
    """
    if not language_code:
        language_code = settings.LANGUAGE_CODE
    languages = dict(settings.LANGUAGES).keys()

    # first try if there is an exact language
    if language_code in languages:
        return language_code

    # otherwise split the language code if possible, so iso3
    language_code = language_code.split("-")[0]
    if not language_code in languages:
        return settings.LANGUAGE_CODE
    return language_code

class MultilingualURLMiddleware(object):
    '''
    See http://ilian.i-n-i.org/language-redirects-for-multilingual-sites-with-django-cms/
    '''
    cached_language_regexp = None

    def get_supported_languages(self):
        return ('fr','en')

    def has_lang_prefix(self, path):
        
        if not self.cached_language_regexp:
            self.cached_language_regexp = re.compile(r"^/(%s)/.*" % "|".join([re.escape(l) for l in self.get_supported_languages()]))

        check = self.cached_language_regexp.match(path)
        
        if check is not None:
            return check.group(1)
        else:
            return False


    def get_language_from_request(self, request):
        
        changed = False
        prefix = self.has_lang_prefix(request.path_info)
        if prefix:
            request.path = "/" + "/".join(request.path.split("/")[2:])
            request.path_info = request.path
            t = prefix
            if t in self.get_supported_languages():
                lang = t
                if hasattr(request, "session") and request.session.get("django_language", None) != lang:
                    request.session["django_language"] = lang
                changed = True
        else:
            lang = translation.get_language_from_request(request)
        
        if not changed:
            if hasattr(request, "session"):
                lang = request.session.get("django_language", None)
                if lang in self.get_supported_languages() and lang is not None:
                    return lang
            
            elif "django_language" in request.COOKIES.keys():
                lang = request.COOKIES.get("django_language", None)
                if lang in self.get_supported_languages() and lang is not None:
                    return lang
        
            if not lang:
                lang = translation.get_language_from_request(request)
        
        return lang

    def process_request(self, request):
        
        path = unicode3(request.path)
        
        if not path in URLS_WITHOUT_LANGUAGE_REDIRECT and \
           not path.startswith(settings.MEDIA_URL) and \
           not path.startswith(settings.STATIC_URL):
            
            
            
            # Parent will rewrite the path to remove the language if found
            # get_full_path() so we include any query string            
            original_path = request.get_full_path()
            
            request_language = self.get_language_from_request(request)
            request.LANGUAGE_CODE = request_language
            translation.activate(request_language)
            
            # manage to remove the language root and patch with host path
            for no_redirect_url in URLS_WITHOUT_LANGUAGE_REDIRECT:
                if original_path.startswith(no_redirect_url):
                    # Path matched, no need for auth
                    logger.debug('Requested path %s in URLS_WITHOUT_LANGUAGE_REDIRECT, '
                                 'skipping language enforcement' % original_path)
                    return None
            
            # at this point we redirect to the language url 
            # only if get or head requests methods
            if request.method not in ('GET', 'HEAD'):
                return
            
            #
            language = getattr(request, 'LANGUAGE_CODE', None)

            # Missing trailing slash
            if original_path == ('/%s' % language):
                return HttpResponseRedirect('/%s/' % language)
            else:
                # Missing trailing slash with query string
                if original_path.startswith('/%s?' % language):  
                    return HttpResponseRedirect('/%s/?%s' % (language, request.META.get('QUERY_STRING', '')))
                
                #
                if not original_path.startswith('/%s/' % language):
                    return HttpResponseRedirect('/%s%s?%s' % (language, request.path, request.META.get('QUERY_STRING', '')))
                #else:
                #    return HttpResponseRedirect('/%s%s' % (language, request.path))

