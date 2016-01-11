# -*- coding: utf-8 -*-
import inspect
import logging
import re
import urllib

from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils import translation

from apetizer.views.action import ActionView
from apetizer.views.api import get_class_that_defined_method


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

    def has_lang_prefix(self, path):
        
        if not self.cached_language_regexp:
            self.cached_language_regexp = re.compile(r"^/(%s)/.*" % "|".join([re.escape(l[0]) for l in self.get_supported_languages()]))

        check = self.cached_language_regexp.match(path)
        
        if check is not None:
            return check.group(1)
        else:
            return False

    def get_supported_languages(self):
        """
        TODO
        get locales from database
        """
        LANGUAGES = [
            ('fr', 'Français'),
            ('en', 'English'),
        ]
        return LANGUAGES

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

        # insert domain path into request.path
        # request.path_info = request.path
        #if not request.path.startswith('/admin/') and not request.path.startswith('/search/'):
        # request.path_info = '/'+request.META['HTTP_HOST'].split(':')[0]+request.path
        #    #request.path = '/'+request.META['HTTP_HOST'].split(':')[0]+request.path

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
                
        lang = get_default_language(lang)
        return lang

    def process_request(self, request):
        
        path = unicode(request.path)
        
        if not path in URLS_WITHOUT_LANGUAGE_REDIRECT and \
           not path.startswith(settings.MEDIA_URL) and \
           not path.startswith(settings.STATIC_URL):
            
            
            
            # Parent will rewrite the path to remove the language if found
            # get_full_path() so we include any query string            
            original_path = request.get_full_path()
            
            request_language = self.get_language_from_request(request)
            request.LANGUAGE_CODE = request_language
            translation.activate(request_language)
            
            #print original_path
            #print request.path
            #print request.path_info
            
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


def patch_response(content, pages_root, language):
    # Customarily user pages are served from http://the.server.com/~username/
    # When a user uses django-cms for his pages, the '~' of the url appears quoted in href links.
    # We have to quote pages_root for the regular expression to match.
    #
    # The used regex is quite complex. The exact pattern depends on the used settings.
    # The regex extracts the path of the url without the leading page root, but only matches urls
    # that don't already contain a language string or aren't considered multilingual.
    #
    # Here is an annotated example pattern (_r_ is a shorthand for the value of pages_root):
    #   pattern:        <a([^>]+)href=("|\')(?=_r_)(?!(/fr/|/de/|/en/|/pt-br/|/media/|/media/admin/))(_r_(.*?))("|\')(.*?)>
    #                     |-\1--|     |-\2-|       |---------------------\3---------------------|    | |-\5--|||-\6-||-\7-|
    #                                                                                                |---\4---|
    #   input (_r_=/):  <a href="/admin/password_change/" class="foo">
    #   matched groups: (u' ', None, u'/admin/password_change/', u'admin/password_change/', u' class="foo"')
    #
    # Notice that (?=...) and (?!=...) do not consume input or produce a group in the match object.
    # If the regex matches, the extracted path we want is stored in the fourth group (\4).
    quoted_root = urllib.quote(pages_root)
    ignore_paths = ['%s%s/' % (quoted_root, l[0]) for l in settings.LANGUAGES]
    ignore_paths += [settings.MEDIA_URL, settings.ADMIN_MEDIA_PREFIX]
    if getattr(settings,'STATIC_URL', False):
        ignore_paths += [settings.STATIC_URL]
        
    HREF_URL_FIX_RE = re.compile(ur'<a([^>]+)href=("|\')(?=%s)(?!(%s))(%s(.*?))("|\')(.*?)>' % (
        quoted_root,
        "|".join([re.escape(p) for p in ignore_paths]),
        quoted_root
    ))

    # Unlike in href links, the '~' (see above) the '~' in form actions appears unquoted.
    #
    # For understanding this regex, please read the documentation for HREF_URL_FIX_RE above.
    
    ignore_paths = ['%s%s/' % (pages_root, l[0]) for l in settings.LANGUAGES]
    ignore_paths += [settings.MEDIA_URL, settings.ADMIN_MEDIA_PREFIX]
    if getattr(settings,'STATIC_URL', False):
        ignore_paths += [settings.STATIC_URL]
    FORM_URL_FIX_RE = re.compile(ur'<form([^>]+)action=("|\')(?=%s)(?!(%s))(%s(.*?))("|\')(.*?)>' % (
        pages_root,
        "|".join([re.escape(p) for p in ignore_paths]),
        pages_root
    ))

    content = HREF_URL_FIX_RE.sub(ur'<a\1href=\2/%s%s\5\6\7>' % (language, pages_root), content)
    content = FORM_URL_FIX_RE.sub(ur'<form\1action=\2%s%s/\5\6\7>' % (pages_root, language), content).encode("utf8")
    return content

