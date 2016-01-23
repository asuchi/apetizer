'''
Created on 15 janv. 2013

@author: rux
'''
from collections import OrderedDict
from datetime import datetime
from hashlib import sha1
import hashlib
import json
import logging
import math
import operator
import os
from time import mktime
import time
import unicodedata
import uuid

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.cache import cache as object_cache
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import File
from django.db import models
from django.db.models.fields import TextField, BooleanField, CharField
from django.db.models.fields.files import ImageField
from django.db.models.manager import Manager
from django.db.models.query import QuerySet
from django.db.models.query_utils import Q
from django.forms.models import model_to_dict
from django.utils import translation
from django.utils.text import get_valid_filename, slugify
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _, get_language
from geopy.distance import EARTH_RADIUS

import apetizer.default_settings as DEFAULTS
from apetizer.forms.frontend import FolderNameField, SubdomainListField
from apetizer.parsers.json import API_json_parser
from apetizer.storages.memcached import MemcacheStorage, DictStorage
from apetizer.utils.compatibility import unicode3


try:
    from urllib.parse import unquote
except:
    from urllib import unquote

logger = logging.getLogger(__name__)

global URLS_PORT
try:
    URLS_PORT = '8000'
except:
    pass

def get_default_storage():
    """
    :return: Drilldown object
    """
    if os.environ.get('DJANGO_ENV', 'dev' ) == 'production':
        storage = MemcacheStorage(object_cache)
    else:
        storage = DictStorage()
    
    return storage

def get_cached_key(key):
    return str(key)

class ObjectTree(dict):
    
    def __init__(self, storage):
        self.storage = storage
        self.__dict__['instances'] = {}
        return super(ObjectTree, self).__init__()

    def __getitem__(self, key):
        return self.__dict__['instances'][key]
        
    def __setitem__(self, key, value):
        self.__dict__['instances'][key] = value
        #self.storage.set_key_data(get_cached_key(key), 'exists')
        
    def __delete__(self, key):
        del self.__dict__['instances'][key]
        # remove the key from the cache
        if self.storage.has_key(get_cached_key(key)):
            self.storage.remove_key_data(get_cached_key(key))

    def __contains__(self, key):
        # check if key in the cache
        if key in self.__dict__['instances']:
            return True
        else:
            return False
            return self.storage.has_key(get_cached_key(key))

global object_tree_cache
object_tree_cache = ObjectTree(get_default_storage())
#object_tree_cache = CoreManager.get_core()

def object_tree_default(path, name, data):
    #return object_tree_cache.getGidDefault(path, name, data)
    return {}
def object_tree_flush():
    #object_tree_cache.flush()
    return
def object_tree_invalidate(path):
    #if not path in object_tree_cache.modifiedGids:
    #    object_tree_cache.modifiedGids.append(path)
    return


def get_new_uuid():
    return str(uuid.uuid4())

def get_distincts(object_list, key):
        
    try:
        object_list.distinct(key)
    except  NotImplementedError:
        pass
    
    # filter by key
    objects_by_key = OrderedDict()
    for o in object_list:
        value = o.__getattribute__(key)
        if not value in objects_by_key.keys():
            objects_by_key[value] = o
    
    #
    objects = []
    for k in objects_by_key:
        objects.append(objects_by_key[k])
    
    return objects
    

def upload_to(instance, filename):
    upload_path = getattr(settings, 'MULTIUPLOADER_FILES_FOLDER', 
                          DEFAULTS.MULTIUPLOADER_FILES_FOLDER)
    
    if upload_path[-1] != '/':
        upload_path += '/'
    
    filename = get_valid_filename(os.path.basename(filename))
    filename, ext = os.path.splitext(filename)
    fhash = sha1(str(time.time())).hexdigest()
    fullname = os.path.join(upload_path, "%s.%s%s" % (filename, fhash, ext))
    
    return fullname

def upload_to_domain(instance, filename):
    upload_path = getattr(settings, 'MULTIUPLOADER_FILES_FOLDER', 
                          DEFAULTS.MULTIUPLOADER_FILES_FOLDER)
    
    if upload_path[-1] != '/':
        upload_path += '/'
    
    folderpath = instance.get_path()

    upload_path = folderpath
    
    filename = get_valid_filename(os.path.basename(filename))
    filename, ext = os.path.splitext(filename)
    fhash = sha1(str(time.time())).hexdigest()
    
    fullname = os.path.join(upload_path, "%s.%s%s" % (filename, fhash, ext))
    
    return fullname


class AuditedModel(models.Model):
    '''
    An abstract model to add creation and modification values
    '''
    # because of django 1.8.4 ...
    #id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id = models.CharField(primary_key=True, default=get_new_uuid, editable=False, max_length=128)
    visible = models.BooleanField(default=True)
    
    #
    ref_time = models.BigIntegerField(editable=False)
    
    created_date = models.DateTimeField(_('created on'), editable=False)
    modified_date = models.DateTimeField(_('modified on'), editable=False, null=True, blank=True)
    completed_date = models.DateTimeField(_('completed on'), editable=False, null=True, blank=True)
    
    class Meta:
        abstract = True
    
    @staticmethod
    def get_ref_time():
        return time.time()*100000
    
    def save(self, *args, **kwargs):
        # Some child implementations (like VersionedModel) want to persist the created_date
        # of the oldest ancestor.  This check thus allows that.
        now_dtz = now()
        
        if not self.created_date:
            self.created_date = now_dtz
        if not self.ref_time:
            self.ref_time = AuditedModel.get_ref_time()
        
        #self.ref_time = time.time()*100000
        self.modified_date = now_dtz
        
        super(AuditedModel, self).save(*args, **kwargs)



class DataPath(AuditedModel):
    
    akey = models.CharField(max_length=128)
    action = models.CharField(max_length=65)
    
    path = models.CharField(max_length=512)
    
    # instance class
    type = models.CharField(max_length=65, default='Thing')
    data = TextField(default={}, blank=True, null=True)
    
    locale = models.CharField(max_length=6)

    geohash = models.CharField(max_length=12, default='', blank=True, null=True)
    
    def __unicode__(self):
        return self.path+'('+self.action+')'
    
    def __init__(self, *args, **kwargs):
        super(DataPath, self).__init__(*args, **kwargs)
    
    def full_clean(self, exclude=None, validate_unique=True):
        
        if not exclude:
            exclude = []
        if not 'related' in exclude:
            exclude.append('related')
        
        super(DataPath, self).full_clean(exclude=exclude, validate_unique=validate_unique)
    
    def save(self, *args, **kwargs):
        if type(self.data) not in (type(''), type(u'')):
            self.data = json.dumps(self.data, default=API_json_parser)
        self.full_clean()
        super(DataPath, self).save(*args, **kwargs)


    def get_distincts(self, object_list, key):
        
        try:
            object_list.distinct(key)
        except  NotImplementedError:
            pass
        
        # filter by email
        objects_by_key = OrderedDict()
        for o in object_list:
            value = o.__getattribute__(key)
            if not value in objects_by_key.keys():
                objects_by_key[value] = o
        
        #
        objects = []
        for k in objects_by_key:
            objects.append(objects_by_key[k])
        
        return objects


    def is_visible(self):
        if self.published == True or self.published == None:
            return True
        else:
            return False
    

class Visitor(DataPath):
    """
    """
    # any visitor may have a parent, from the referer url to any other visitor
    email = models.EmailField(max_length=156, blank=True, null=True)
    username = models.CharField(max_length=65, blank=True, null=True)
    
    # should be moved to moderation
    validated =  models.DateTimeField(_('Date de validation'), blank=True, null=True)
    
    # credits ?
    credits = 0
    
    def save(self, *args, **kwargs):
        super(Visitor, self).save(*args, **kwargs)

    def get_url(self):
        return self.get_profile_item().get_url()

    def get_roots(self):
        contributions = self.get_contributions()
        root_ids = list(set([c.related.get_root().id for c in contributions]))
        return Item.objects.filter(parent=None, id__in=root_ids, visible=True)

    def get_profile_item(self):
        
        user_profile_hash = self.get_hash()
        try:
            user_profile_item = Item.objects.filter(parent=None, slug=user_profile_hash).order_by('-modified_date')[0]
        except IndexError:
            
            if not self.username:
                username = 'Anonyme'
            else:
                username = self.username
            
            user_profile_item = Item(akey=self.akey,
                                     parent=None,
                                     slug=user_profile_hash,
                                     label='Visiteur',
                                     title=username,
                                     status='added',
                                     username=self.username,
                                     email=self.email,
                                     locale=self.locale,
                                     action='profile',
                                     path=self.path,
                                     visible=False,
                                     published=False,
                                     validated=self.validated,
                                     )
            user_profile_item.save()
            
        
        if user_profile_item.visible:
            user_profile_item.visible = False
        
        return user_profile_item
    
    def get_token(self):
        # returns a hash based on the user email if exists
        if self.email:
            return hashlib.md5(hashlib.sha1(settings.SECRET_KEY+self.akey+self.email).hexdigest()).hexdigest()
        else:
            return hashlib.md5(hashlib.sha1(settings.SECRET_KEY+self.akey).hexdigest()).hexdigest()

    def get_hash(self):
        # returns a hash based on the user email if valid
        if self.email and self.validated:
            return hashlib.md5(settings.SECRET_KEY+self.email).hexdigest()
        else:
            return hashlib.md5().hexdigest()

    def is_valid_token(self, token):
        return self.get_token() == token

    def get_first_name(self):
        if not self.username:return ''
        return self.username.split(' ')[0]

    def get_last_name(self):
        if not self.username:return ''
        return ' '.join(self.username.split(' ')[1:])
    
    def get_full_name(self):
        item = self.get_profile_item()
        if self.username and self.validated:
            if item.title != self.username and self.email and self.validated:
                return self.username+' ('+item.title+')'
            else:
                return self.username

        elif self.email:
            return '@nonyme'
        else:
            return 'Anonyme'

    def get_image(self):
        item = self.get_profile_item()
        if item.image:
            return item.image
        else:
            return File(settings.STATIC_ROOT+'/images/anonymous.png')
    
    def get_all_keys(self):
        
        akeys = [self.akey,]
        
        if self.email:
            distinct_sessions = self.get_distincts( Visitor.objects.filter(email=self.email), 'akey')
            for s in distinct_sessions:
                akeys.append(s.akey)
        
        return akeys
    
    def get_feed(self):
        if self.email and self.validated:
            #query = Q(akey=self.akey) | Q(email=self.email) | Q(related__email=self.email) | Q(related__akey=self.akey)
            query = Q(email=self.email) | Q(related__email=self.email) | Q(akey=self.akey) | Q(related__akey=self.akey)
        else:
            query = Q(akey=self.akey) | Q(related__akey=self.akey)
        feed = Moderation.objects.filter(query).order_by('-modified_date')[0:50]
        return feed
    
    def get_proposals(self):
        """
        Get my creation list
        """
        proposal_status = ('proposed',)
        if self.email and self.validated:
            proposals = Moderation.objects.filter(email=self.email, status__in=proposal_status).order_by('-modified_date')
        else:
            proposals = Moderation.objects.filter(akey=self.akey, status__in=proposal_status).order_by('-modified_date')
        return proposals
    
    def get_proposed(self):
        """
        Get my creation list
        """
        proposal_status = ('proposed', 'accepted', 'rejected',)
        if self.email and self.validated:
            proposals = Moderation.objects.filter(status__in=proposal_status, related__email=self.email).order_by('-modified_date')
        else:
            proposals = Moderation.objects.filter(status__in=proposal_status, related__akey=self.akey).order_by('-modified_date')
        return proposals


    def get_contributions(self):
        """
        Get my contributions list
        """
        contribution_status = ('added', 'changed', 'accepted', 'uploaded')
        
        if self.email and self.validated:
            contribs = Moderation.objects.filter(email=self.email, status__in=contribution_status, visible=True, related__visible=True).order_by('-modified_date')
        else:
            contribs = Moderation.objects.filter(akey=self.akey, status__in=contribution_status, visible=True, related__visible=True).order_by('-modified_date')
            
        return self.get_distincts(contribs, 'related_id')
    

    def get_subscriptions(self):
        """
        Get my subscriptions list
        """
        subscription_status = ('subscribed', )
        if self.email and self.validated:
            contribs = Moderation.objects.filter(email=self.email, status__in=subscription_status, visible=True, related__visible=True).order_by('-modified_date')
        else:
            contribs = Moderation.objects.filter(akey=self.akey, status__in=subscription_status, visible=True, related__visible=True).order_by('-modified_date')
        
        return self.get_distincts(contribs, 'related_id')


    def get_memberships(self):
        return []
        # get root group where the user is member
        relateds = self.get_subscriptions()
        
        roots = []
        for sub in relateds:
            if not sub.related.get_root() in roots:
                roots.append(sub.related.get_root())
        
        return roots


    def get_messages(self):
        """
        Get my messages
        """
        messages_status = ('contact',)
        if self.email and self.validated:
            contribs = Moderation.objects.filter(related__email=self.email, status__in=messages_status).order_by('-modified_date')
        else:
            contribs = Moderation.objects.filter(related__akey=self.akey, status__in=messages_status).order_by('-modified_date')
        return contribs


    def get_todos(self):
        """
        Get my todo list
        """
        subscription_status = ('comment', 'modified', 'changed', 'published', 'added')
        if self.email and self.validated:
            contribs = Moderation.objects.filter(email=self.email, status__in=subscription_status, subscribed=True).order_by('-modified_date')
        else:
            contribs = Moderation.objects.filter(akey=self.akey, status__in=subscription_status, subscribed=True).order_by('-modified_date')
        return contribs   



class Moderation(Visitor):
    """
    Respresents a user comment or item changes
    """
    # moderation related
    origin = models.ForeignKey("Moderation", null=True, blank=True, related_name='replys')
    
    # item related
    related = models.ForeignKey("Item", related_name="events")
    
    # unread, reviewing, validated, rejected
    # or any other string ...
    status = models.CharField(max_length=20, default='')

    #
    subject = models.CharField(max_length=156, blank=True, null=True)
    message = models.CharField(max_length=4048, blank=True, null=True)
    
    evaluation = models.IntegerField(default=0, blank=True)
    subscribed = models.NullBooleanField(default=True, blank=True)
    
    is_busy = models.NullBooleanField(default=False, editable=False)
    is_sent = models.NullBooleanField(default=False, editable=False)
    
    def __getattr__(self, key):
        
        if key in ('related',):
            if self.related_id and not self.related_id in object_tree_cache:
                object_tree_cache[self.related_id] = super(Moderation, self).__getattr__(key)
            return object_tree_cache[self.related_id]
        
        return super(Moderation, self).__getattr__(key)
    
    def get_url(self):
        if self.related_id:
            return self.related.get_url()
        else:
            return super(Moderation, self).get_url()
    
    def get_author(self):
        return self.visitor_ptr
    
    def full_clean(self, exclude=None, validate_unique=True):        
        super(Moderation, self).full_clean(exclude=exclude, validate_unique=validate_unique)
        
    def save(self, *args, **kwargs):
        super(Moderation, self).save(*args, **kwargs)
    
    

class Translation(Moderation):
    
    slug = models.CharField(max_length=128, default='', blank=False)
    
    label = models.CharField(max_length=65)
    title = models.CharField(max_length=156)
    
    description = models.TextField(blank=True)
    content = models.TextField(blank=True, null=False)
    
    redirect_url = models.TextField("Redirection url", blank=True, null=False)
    
    def get_url(self, language=None):
        if language == None:
            language = self.locale
        return self.related.get_url(language=language)

    def full_clean(self, *args, **kwargs):
        
        # check for correct slug
        if not self.slug:
            if self.label == self.title and self.label:
                self.slug = slugify(self.label)
            else:
                self.slug = slugify(self.label+'-'+self.title)
        
        return super(Translation, self).full_clean(*args, **kwargs)
    
    def save(self, *args, **kwargs):
        
        # check for correct slug
        if not self.slug:
            if self.label == self.title and self.label:
                self.slug = slugify(self.label)
            else:
                self.slug = slugify(self.label+'-'+self.title)
        
        super(Translation, self).save(*args, **kwargs)
        
        # update translation
        if self.related and self.related.get_uid_path() in object_tree_cache \
            and 'translations' in object_tree_cache[self.related.get_uid_path()]:
            related_data = object_tree_cache[self.related.get_uid_path()]
            related_data['translations'][self.locale] = self
            object_tree_cache[self.related.get_uid_path()] = related_data
        
    def __unicode__(self):
        return self.slug+' - '+self.locale

    def get_author(self):
        author_status = ('added', 'modified', 'changed', 'created', 'claimed', 'imported')
        try:
            author = Moderation.objects.filter(related_id=self.related_id, status__in=author_status, validated__isnull=False).order_by('-created_date')[0]
        except IndexError:
            try:
                author = Moderation.objects.filter(related_id=self.related_id, status__in=author_status).order_by('-created_date')[0]
            except IndexError:
                try:
                    author = Moderation.objects.filter(related_id=self.related_id,).order_by('-created_date')[0]
                except IndexError:
                    author = self
        return author


class TreeManager(Manager):
    
    tree_cache = {}
    
    def fixCase(self, st):
        return ' '.join(''.join([w[0].upper(), w[1:].lower()]) for w in st.split())

    def get_clean_path(self, url):
        
        url = unquote(url)
        
        if url in ('', '/'):
            return ''
        # filter out possible parameters
        cleanUrl = url.split( '?' )[0]
        # handle possible anchor
        cleanUrl = cleanUrl.split( '#' )[0]
        
        # remove possible start slash
        while cleanUrl[0] == '/':
            cleanUrl = cleanUrl[1:]
        # remove possible end slash
        while cleanUrl[-1:] == '/':
            cleanUrl = cleanUrl[:-1]
        
        cleanUrl.replace('//', '/')
        # remove forbidden slugs
        # TODO
        return cleanUrl

    def get_at_url(self, url, exact=True):
        
        # check for uids in url
        parent = None
        # filter out possible parameters
        cleanUrl = self.get_clean_path(url)
        try:
            item = TreeManager.tree_cache[cleanUrl]
            return item
        except:
            pass
        
        slug = None
        # split url
        parts = cleanUrl.split('/')
        if len(parts) == 1:
            slug = parts[0]
        else:
            slug = parts[-1]
            basePath = '/'
            for part in parts[:-1]:
                basePath += part+'/'
                try:
                    parent = self.get_at_url(basePath, exact=True)
                except:
                    slug = part
                    break

        # get corresponding slugs
        translations = Translation.objects.filter(slug=slug, related__parent=parent)
        item = None
        # filter correct one with corresponding parent
        if len(translations):
            for translation in translations:
                # find first with same parent
                if translation.related and translation.related.parent == parent:
                    item = translation.related
                    break
                else:
                    if not exact:
                        item = parent
        else:
            if not exact:
                item = parent
        
        if item is None:
            raise ObjectDoesNotExist()
        
        TreeManager.tree_cache[cleanUrl] = item
        TreeManager.tree_cache[item.get_path()] = item
        TreeManager.tree_cache[item.get_url()] = item
        TreeManager.tree_cache[item.get_uid_url()] = item
        
        return item


    def get_or_create_url(self, url, **kwargs):
        
        # filter out possible parameters
        cleanUrl = self.get_clean_path(url)
        
        try:
            return TreeManager.tree_cache[cleanUrl]
        except:
            pass
        
        slug = None
        
        # split url
        parts = cleanUrl.split('/')
        baseItem = None
        if len(parts) == 1:
            slug = parts[0]
            translations = Translation.objects.filter(slug=slug, related__parent=None)
        else:
            slug = parts[-1]
            basePath = ''
            for part in parts[:-1]:
                basePath = basePath+'/'+part
                baseItem = self.get_or_create_url(basePath, **kwargs)
            
            translations = Translation.objects.filter(slug=slug, related__parent=baseItem)
        
        parent = baseItem

        # get corresponding slugs
        #translations = Translation.objects.filter(slug=slug)
        #translations = Translation.objects.filter(path='/'.join(parts[:-1]))

        # filter correct one with corresponding parent
        if len(translations):
            for translation in translations:
                # find first
                if translation.related and translation.related.parent == parent:
                    TreeManager.tree_cache[cleanUrl] = translation.related
                    return translation.related
        
        item = self.create_item(parent, slug, **kwargs)
        
        TreeManager.tree_cache[url] = item
        TreeManager.tree_cache[cleanUrl] = item
        TreeManager.tree_cache[item.get_url()] = item
        
        return item

    def create_item(self, parent, slug, **kwargs):
        
        label = slug.capitalize()
        
        item = Item(parent=parent, slug=slug, label=label, title=label, **kwargs['pipe'])
        
        #item.locale = kwargs['pipe'].get('locale', get_default_language())
        
        #item.action = kwargs['pipe']['action']
        #item.path = kwargs['pipe']['path']
        #item.akey = kwargs['pipe']['akey']
        
        item.status = 'created'
        
        item.full_clean()
        item.save()
        
        return item



'''
Constants for bounding box calcs
'''
MIN_LAT = math.radians(-90)
MAX_LAT = math.radians(90)
MIN_LON = math.radians(-180)
MAX_LON = math.radians(180)


class LocationManager(TreeManager):
    
    def get_query_set(self):
        return SearchQuerySet(model=self.model).exclude(latitude=0.0,longitude=0.0)
        
    def _define_sqlite_geodistance(self):
        '''
        Since SQLite doesn't have a procedural language, we must define our own
        geodistance function for it from python
        '''
        from django.db import connection
        from geopy.distance import GreatCircleDistance
        
        def geodistance(alat, alon, blat, blon):
            return GreatCircleDistance((alat, alon), (blat, blon)).meters
        
        connection.connection.create_function('geodistance', 4, geodistance) #@UndefinedVariable

    def bounding_box(self, location, distance):
        '''
        Given a Location and a distance in meters, return a bounding box as a pair of tuples: 
        ((min lat, min lon), (max lat, max lon)).  All coordinates are in degrees.
        
        Based on http://janmatuschek.de/LatitudeLongitudeBoundingCoordinates
        '''
        dlat = distance / (EARTH_RADIUS * 1000)
        rlat = math.radians(location.latitude)
        min_lat = rlat - dlat
        max_lat = rlat + dlat
        if min_lat > MIN_LAT and max_lat < MAX_LAT:
            dlon = math.asin(math.sin(dlat) / math.cos(math.radians(location.latitude)))
            rlon = math.radians(location.longitude)
            min_lon = rlon - dlon
            max_lon = rlon + dlon
            if min_lon < MIN_LON:
                min_lon = min_lon + (2 * math.pi)
            if max_lon > MAX_LON:
                max_lon = max_lon - (2 * math.pi)
        else:
            # poles are within the distance
            min_lat = max(min_lat, MIN_LAT)
            max_lat = min(max_lat, MAX_LAT)
            min_lon = MIN_LON
            max_lon = MAX_LON

        return ((math.degrees(min_lat), math.degrees(min_lon)), (math.degrees(max_lat), math.degrees(max_lon)))
    
    def near(self, location, distance=10000, order_by_distance=False):
        """
        Returns a list of Locations near a given Location, within a certain
        distance.  Distance is in meters.  Uses the fuzzy lat/long if directed
        to do so.
        """
        #return SearchQuerySet(self.model())
        if location is None or distance is None or not location.latitude or not location.longitude:
            #return SearchQuerySet(self.model())
            return self.get_query_set()
            #return super(LocationManager, self).get_empty_query_set()
            
        # The location we're searching near won't ever use the fuzzy lat/long, just the results
        latitude = location.latitude
        longitude = location.longitude
        
        #queryset = super(LocationManager, self).get_query_set()
        queryset = self.get_query_set()
        
        # Exclude ourselves if we are the same kind of location object
        if isinstance(location, self.model) and hasattr(location, 'id') and location.id:
            queryset = queryset.exclude(id=location.id)
        
        # prune down the set of all locations to something we can quickly check precisely.
        # the database should prefer a range scan of the indexes on these columns prior to 
        # running the geodistance function on the remainder.
        bounding_box = self.bounding_box(location, distance)
    
        lat_function_name = 'latitude'
        lon_function_name = 'longitude'
        queryset = queryset.filter(
            latitude__range = (bounding_box[0][0], bounding_box[1][0]), 
            longitude__range = (bounding_box[0][1], bounding_box[1][1])
        )
        # we should use geohash here to filter geo
        
        # Must define a python function for sqlite instead of using built-in db function
        if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
            self._define_sqlite_geodistance()

        # Build call to custom geodistance SQL function for our table.latitude/table.longitude
        latlng_table = self.model._meta.get_field_by_name('latitude')[0].model._meta.db_table
        geodistance_select_clause = 'geodistance(%%s, %%s, "%s"."%s", "%s"."%s")' \
            % (latlng_table, lat_function_name, latlng_table, lon_function_name)
        geodistance_where_clause = geodistance_select_clause + ' <= %s'
        
        
        queryset = queryset.extra(select={'distance': geodistance_select_clause}, 
                                  select_params=(latitude, longitude, distance),
                                  where=[geodistance_where_clause], 
                                  params=[latitude, longitude, distance])
        
        if order_by_distance:
            queryset = queryset.order_by('distance')

        return queryset


def get_default_language():
    return get_language()


DATETIME_FORMATS = (('%Y-%m-%d %H:%M:%S'),)

class Item(Translation):
    """
    The model for a content item
    """
    __root__ = None
    __dirty__ = False
    
    parent = models.ForeignKey('self', editable=True, blank=True, null=True, related_name='children')
    
    geojson = models.TextField(verbose_name=_('GeoJSON data field'), null=True, blank=True)
    image = ImageField(upload_to=upload_to, blank=True, null=True)
    file = models.FileField(upload_to=upload_to, max_length=255, blank=True, null=True)
    
    # representation
    behavior = models.CharField(max_length=65, default='view')
    published = models.NullBooleanField(blank=True)
    order = models.IntegerField(default=0)
    
    # bridge
    related_url = models.URLField(verbose_name=_('Related URL'), null=True, blank=True)
    related_cron = models.CharField(max_length=65, default='live', choices=(('live','Au chargement'),
                                                                            ('once','Une fois'),
                                                                            ('every-hour','Toutes les heures'),
                                                                            ('every-day','Tous les jours'),
                                                                            ('every-week','Une fois par semaine'),
                                                                            ('every-month','Bon ben tous les mois ...'),
                                                                            ))
    
    
    # event
    start = models.DateTimeField(verbose_name=_('Start Date'), null=True, 
                                 blank=True)
    end = models.DateTimeField(verbose_name=_('End Date'), null=True,
                               blank=True)
    
    
    @property
    def start_timestamp(self):
        """
        Return end date as timestamp
        """
        if self.start:
            return datetime_to_timestamp(self.start)
        else:
            return datetime_to_timestamp(self.created_date)

    @property
    def end_timestamp(self):
        """
        Return end date as timestamp
        """
        if self.end:
            return datetime_to_timestamp(self.end)
        else:
            return datetime_to_timestamp(self.modified_date)

    
    def __unicode__(self):
        return unicode3(self.path)

    objects = LocationManager()
    
    __inited__ = False
    __localizable__ = ['slug', 'label', 'title', 'description', 'content', 'redirect_url']
    
    def __init__(self, *args, **kwargs):
        super(Item, self).__init__(*args, **kwargs)
        #self.set_cache_data()
        self.__inited__ = True
        #self.get_translation()
    
    class Meta:
        ordering = ('order',)
    
    def __getattribute__(self, attr):
        
        #return super(Item, self).__getattribute__(attr)
        
        # avoid looping on attribute
        if attr in ('__localizable__', '__inited__', '__dict__'):
            return super(Item, self).__getattribute__(attr)
        
        elif attr in ('parent',):
            if self.parent_id:
                if not self.parent_id in object_tree_cache:
                    object_tree_cache[self.parent_id] = super(Item, self).__getattribute__(attr)
                return object_tree_cache[self.parent_id]
            else:
                return None
        
        # return convenient translation
        elif attr in self.__localizable__:
            trans = self.get_translation()
            if trans != self:
                return trans.__getattribute__(attr)
            else:
                return super(Item, self).__getattribute__(attr)
        else:
            return super(Item, self).__getattribute__(attr)
    
    def __getattr__(self, key):
        if key in ('parent',):
            if not self.parent_id in object_tree_cache:
                object_tree_cache[self.parent_id] = super(Item, self).__getattr__(key)
            return object_tree_cache[self.parent_id]
        
        return super(Item, self).__getattr__(key)
    
    def __setattr__(self, attr, value):
        
        if attr in self.__localizable__ and self.__inited__:
            trans = self.get_translation()
            if trans != self:
                # mark translation as dirty
                trans.__setattr__(attr, value)
            else:
                return super(Item, self).__setattr__(attr, value)
        else:
            return super(Item, self).__setattr__(attr, value)
    
    
    def delete(self, *args, **kwargs):
        
        uidpath = self.get_uid_path()
        
        super(Item, self).delete(*args, **kwargs)
        
        # purge caches
        
        if uidpath in object_tree_cache:
            del object_tree_cache[uidpath]
        
        if self.parent and self.parent.get_uid_path() in object_tree_cache and 'children' in object_tree_cache[self.parent.get_uid_path()]:
            parent_data = object_tree_cache[self.parent.get_uid_path()]
            del parent_data['children']
            del parent_data['children_qs']
            del parent_data['children_count']
            object_tree_cache[self.parent.get_uid_path()] = parent_data
        
    def full_clean(self, *args, **kwargs):
        if not self.related_id:
            self.related_id = self.id
        return super(Item, self).full_clean(*args, **kwargs)
        

    def save(self, *args, **kwargs):
        
        #if not self.related_id:
        #    self.related_id = self.id
        
        if not self.path:
            self.path = self.get_path()
        
        super(Item, self).save(*args, **kwargs)
        
        trans = self.get_translation()
        if trans != self:
            trans.save()
        
        #if self.parent:
        #    self.parent.set_cache_data()
        
        #return
        #
        #data = model_to_dict(self)
        data = {}
        data['name'] = self.id
        
        if self.parent:
            data['path'] = self.parent.get_uid_path()
        else:
            data['path'] = '/'
        
        object_tree_cache[self.get_uid_path()] = object_tree_default(data['path'], data['name'], data)
        object_tree_flush()
        
        # purge caches
        if self.get_uid_path() in object_tree_cache and 'translations' in object_tree_cache[self.get_uid_path()]:
            t_data = object_tree_cache[self.get_uid_path()]
            del t_data['translations']
            return t_data
        #if self.parent and self.parent.get_uid_path() in object_tree_cache:
        #    del object_tree_cache[self.parent.get_uid_path()]
        
        
        #return

    
    def get_root(self):
        if self.parent_id == None:
            return self
        if not self.__root__:
            self.__root__ = self.parent.get_root()
        return self.__root__
    
    def get_image(self):
        if self.image:
            return self.image
        else:
            return super(Item, self).get_image()
    
    def get_ancestors(self, ascending=None, include_self=False):
        if self.parent_id == None:
            if include_self:
                return [self]
            else:
                return []
        else:
            ancestors = self.parent.get_ancestors()
            ancestors.append(self.parent)
            if include_self:
                ancestors.append(self)
            
            return ancestors
    
    def set_cache_object(self):
        if self.parent_id and not self.parent.get_uid_path() in object_tree_cache:
            self.parent.set_cache_data()
        self.set_cache_data()

    def get_cache_data(self):
        if self.__inited__ and not self.get_uid_path() in object_tree_cache:
            self.set_cache_data()
        return object_tree_cache[self.get_uid_path()]
    
    def set_cache_data(self):
        
        # check for parent data
        #if self.parent and not self.parent.get_uid_path() in object_tree_cache:
        #    self.parent.set_cache_data()
        
        #data = model_to_dict(self)
        data = {}
        data['name'] = self.id
        
        if self.parent_id:
            data['path'] = self.parent.get_uid_path()
        else:
            data['path'] = '/'
        
        gid_data = object_tree_default(data['path'], data['name'], data)
        object_tree_cache[self.get_uid_path()] = gid_data
        
        object_tree_flush()
        
        return gid_data
    
    def get_descendants(self):
        """
        Get all the descendants items
        """
        node_data = self.get_cache_data()
        
        if not 'descendants_qs' in node_data:
            
            qs = QuerySet(model=self.__class__)
            
            parent_keys = ['parent_id']
            parent_key = 'parent_id'
            parent_dict = {parent_key:self.id}
            while Item.objects.filter(**parent_dict).exists():
                parent_key = 'parent__'+parent_key
                parent_dict = {parent_key:self.id}
                parent_keys.append(parent_key)
            
            qgroup = reduce(operator.or_,
                            (Q(**{fieldname: self.id}) for fieldname in parent_keys))
            
            qs = qs.filter(qgroup, visible=True)
            
            node_data['descendants_qs'] = qs
            node_data['descendants_count'] = qs.count()
            
            object_tree_invalidate(self.get_uid_path())
        
        return node_data['descendants_qs']
    
    def get_descendants_count(self):
        
        if not self.get_uid_path() in object_tree_cache \
            or not 'descendants_count' in object_tree_cache[self.get_uid_path()]:
            self.get_descendants()
        return object_tree_cache[self.get_uid_path()]['descendants_count']
    
    def get_parents(self):
        if self.parent:
            return self.parent.get_children()[:10]
        else:
            return Item.objects.filter(parent=None, visible=True)[:10]

    def get_children(self):
        """
        Returns the children QS
        """
        node_data = self.get_cache_data()
        if not 'children_qs' in node_data:
            node_data['children_qs'] = Item.objects.filter(parent=self, visible=True).order_by('order', 'label')
            node_data['children_count'] = node_data['children_qs'].count()
            object_tree_invalidate(self.get_uid_path())
        
        return node_data['children_qs']

    def get_children_count(self):
        if not self.get_uid_path() in object_tree_cache \
            or not 'children_count' in object_tree_cache[self.get_uid_path()]:
            self.get_children()
        return object_tree_cache[self.get_uid_path()]['children_count']

    def is_leaf_node(self):
        return self.get_children_count() == 0
    
    
    latitude = models.FloatField(_(u'latitude'), blank=True, null=True)
    longitude = models.FloatField(_(u'longitude'), blank=True, null=True)
    
    distance = 0
    
    keywords = ['level1','level2','level3','level4']
    
    @property
    def admin0(self):
        return 'root'

    @property
    def admin1(self):
        if self.parent:
            return self.get_root().label
        else:
            return self.label
    
    @property
    def admin2(self):
        if self.parent:
            return self.parent.label
        else:
            return self.label
    
    @property
    def admin3(self):
        if self.parent:
            return self.parent.label
        else:
            return self.label
    
    def get_data(self):
        """
        return the data conbtained in item as a python object
        
        # TODO use the apetizer.parsers.jsonparser
        """
        return json.loads(self.data)
    
    def set_data(self, value):
        """
        return the data conbtained in item as a python object
        
        # TODO use the apetizer.parsers.jsonparser
        """
        self.data = json.dumps(value)
    
    
    def get_translation(self, locale=None):
        
        if locale is None:
            locale = get_default_language()
        
        if not self.related_id:
            return self
        
        if not self.get_uid_path() in object_tree_cache:
            return self

        node_data = self.get_cache_data()
        try:
            return node_data['translations'][locale]
        except:
            if not 'translations' in node_data:
                node_data['translations'] = {}
            
            if locale in node_data['translations']:
                trans = node_data['translations'][locale]
            else:
                try:
                    trans = Translation.objects.filter(related_id=self.id, locale=locale).order_by('-created_date')[0]
                except IndexError:
                    trans = self
                node_data['translations'][locale] = trans
            
            return node_data['translations'][locale]

    def get_translations(self):
        return Translation.objects.filter(related_id=self.id).order_by('-created_date')
    
    def get_absolute_url(self):
        return self.get_url()
    
    __url__ = None
    
    def get_url(self, language=None):
        
        if self.parent_id == None:
            return self.get_uid_url(language)
        
        if self.parent_id == None and self.published == False and self.visible == False:
            return self.get_uid_url(language)
        
        root_node = self.get_root()
        if root_node.visible == False or root_node.slug == root_node.get_hash():
            return self.get_uid_url(language)
        
        if language == None:
            language = self.locale
        
        path = self.get_path()
        
        if not language and self.__url__:
            return self.__url__
        
        if getattr(settings, 'APETIZER_ABSOLUTE', True) == False:
            return path
        
        #if not language:
        #    return '//'+path+'/'
        #else:
        parts = path.split('/')
        domain = parts[0]
        
        if settings.DEBUG:
            domain = domain+':'+URLS_PORT
        
        path = '//'+domain+'/'+language+'/'
        if len(parts) > 1:
            path += '/'.join(parts[1:])+'/'
        
        self.__url__ = path
        
        return path
    
    def get_uid_url(self, language=None):
        if language == None:
            return '/'+self.id+'/'
        else:
            return '/'+language+'/'+self.id+'/'

    def get_uid_path(self):
        return '/'+self.id
        if not self.parent:
            return '/'+self.id
        else:
            return self.parent.get_uid_path()+'/'+self.id

    def get_path(self):
        path = self.slug
        parentObject = self.parent
        while parentObject != None and parentObject.parent != parentObject:
            path = parentObject.slug+'/'+path
            parentObject = parentObject.parent
        return path

    def get_proposals(self):
        proposals = Moderation.objects.filter(related=self.related, status__in=('proposed',),).order_by('-created_date')
        return self.get_distincts(proposals, 'action')

    def get_visits(self):
        visitors = DataPath.objects.filter(path=self.get_url(), action__in=('view',), visible=True)
        return self.get_distincts(visitors, 'akey')

    def get_visitors(self):
        visitors = Visitor.objects.filter(path=self.get_url(), visible=True)
        return self.get_distincts(visitors, 'email')

    def get_contributors(self):
        """
        Get a contributor list
        """
        contribution_status = ('added', 'modified', 'changed', 'accepted', 'rejected')
        contribs = Moderation.objects.filter(related=self, status__in=contribution_status, visible=True).order_by('-ref_time')
        return self.get_distincts(contribs, 'email')
    
    def get_subscribers(self):
        subscribers_status = ('subscribed', )
        subscribers = Moderation.objects.filter(related=self, status__in=subscribers_status, visible=True).order_by('-ref_time')
        return self.get_distincts(subscribers, 'email')

    def get_comments(self):
        comments = Moderation.objects.filter(related=self, status__in=('commented', 'invited'), visible=True).order_by('ref_time')
        return comments
    
    def get_discussion(self):
        messages = Moderation.objects.filter(related=self, status='told', visible=True).order_by('created_date')
        return messages
    
    def get_history(self):
        comments = Moderation.objects.filter(related=self, visible=True).exclude(status__in=('contact','told')).order_by('ref_time')
        return comments
    
    def get_reviewers(self):
        comments = Moderation.objects.filter(related=self, status__in=('accepted', 'rejected'), visible=True).order_by('-ref_time')
        return self.get_distincts(comments, 'email')

    def get_evaluations(self):
        comments = Moderation.objects.filter(related=self, status__in=('evaluated'), visible=True).order_by('-ref_time')
        return self.get_distincts(comments, 'email')



# TODO
    # Manage cost
    # cost = 1
    # price = 1
    # reward = 1
    # unit = 'credit'
    
    # per-hour
    # per-day
    # per-week
    # per-month
    
    # per-view
    # per-add
    # per-{action}
    # per-book
    # 
    

'''
Search methods
'''
class SearchQuerySet(QuerySet):
    '''
    Represents a search for vehicles by parking address
    '''
    def __init__(self, model=None, query=None, using=None, hints=None):
        super(SearchQuerySet, self).__init__(model=model, query=query, using=using, hints=hints)
        self.search_options = {}

    def _clone(self, klass=None, setup=False, **kwargs):
        c = super(SearchQuerySet,self)._clone(klass=klass, setup=setup, **kwargs)
        c.search_options = self.search_options
        # Emulate EmptyQuerySet by cloning in the specific case of an empty _result_cache
        if self.is_empty:
            c._result_cache = self._result_cache
        return c

    @property
    def is_empty(self):
        return self._result_cache is not None and len(self._result_cache) == 0




"""
Monkey-patch the Site object to include a list of subdomains

Future ideas include:

* Site-enabled checkbox
* Site-groups
* Account subdomains (ala basecamp)
"""

# not sure which is better...
# Site.add_to_class('subdomains', SubdomainListField(blank=True))

class Frontend(Site):
    
    # enhance django site model
    folder_name = FolderNameField(blank=True)
    subdomains = SubdomainListField(blank=True)
    
    published = BooleanField(default=False)
    
    login = CharField(max_length=12, default='bee')
    password = CharField(max_length=12, default='honeypot')
    
    @property
    def has_subdomains(self):
        return len(self.subdomains)
    
    @property
    def default_subdomain(self):
        """
        Return the first subdomain in self.subdomains or '' if no subdomains defined
        """
        if len(self.subdomains):
            if self.subdomains[0]=="''":
                return ''
            return self.subdomains[0]
        return ''


def timestamp_to_datetime(timestamp):
    """
    Converts string timestamp to datetime
    with json fix
    """
    if isinstance(timestamp, (str, unicode)):

        if len(timestamp) == 13:
            timestamp = int(timestamp) / 1000

        return datetime.fromtimestamp(timestamp)
    else:
        return ""


def datetime_to_timestamp(date):
    """
    Converts datetime to timestamp
    with json fix
    """
    if isinstance(date, datetime):

        timestamp = mktime(date.timetuple())
        json_timestamp = int(timestamp) * 1000

        return '{0}'.format(json_timestamp)
    else:
        return ""


def strip_accents(s):
    try:
        return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    except:
        logger.debug('NOT UNICODE')
        logger.debug(s)


def FixCase(st):
    return ' '.join(''.join([w[0].upper(), w[1:].lower()]) for w in st.split())



class ModelDiffMixin(object):
    """
    A model mixin that tracks model fields' values and provide some useful api
    to know what fields have been changed.
    """

    def __init__(self, *args, **kwargs):
        super(ModelDiffMixin, self).__init__(*args, **kwargs)
        self.__initial = self._dict

    @property
    def diff(self):
        d1 = self.__initial
        d2 = self._dict
        diffs = [(k, (v, d2[k])) for k, v in d1.items() if v != d2[k]]
        return dict(diffs)

    @property
    def has_changed(self):
        return bool(self.diff)

    @property
    def changed_fields(self):
        return self.diff.keys()

    def get_field_diff(self, field_name):
        """
        Returns a diff for field if it's changed and None otherwise.
        """
        return self.diff.get(field_name, None)

    def save(self, *args, **kwargs):
        """
        Saves model and set initial state.
        """
        super(ModelDiffMixin, self).save(*args, **kwargs)
        self.__initial = self._dict

    @property
    def _dict(self):
        return model_to_dict(self, fields=[field.name for field in
                             self._meta.fields])
