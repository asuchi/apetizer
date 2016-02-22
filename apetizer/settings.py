import os
APPEND_SLASH = False
DEBUG = True
USE_TZ = True
ROOT_URLCONF = "apetizer.urls"
SECRET_KEY = "fsldjkhgljkfshfgnlcuqsngfiu"
ALLOWED_HOSTS = [ "*"]
WEB_ROOT = "www"
STATIC_ROOT = "static"
STATIC_URL = "/static/"
MEDIA_ROOT = "media"
MEDIA_URL = "/media/"
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.contenttypes",
    "django.contrib.humanize",
    "django.contrib.messages",
    "django.contrib.sitemaps",
    "django.contrib.staticfiles",
    "markdown_deux",
    "easy_thumbnails",
    "leaflet",
    "apetizer",
    "dashboard",
]

MIDDLEWARE_CLASSES = [
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.locale.LocaleMiddleware", # Cookie-based, for anonymous users
    
    'apetizer.middleware.multisite.DynamicSitesMiddleware',
    "apetizer.middleware.multilingual.MultilingualURLMiddleware",
    "apetizer.middleware.redirect.ItemRedirect",
    "apetizer.middleware.profiler.CProfileMiddleware",
]


SITES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sites')

DEFAULT_HOST = 'localhost'

HOSTNAME_REDIRECTS = {
     'planrecup.com': 'www.planrecup.com',
}
ENV_HOSTNAMES = {
    'biodigitals.dev':    'biodigitals',
}

WSGI_APPLICATION = "wsgi.application"
DATABASES = {
    'default':{
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'apetizer.db',
     },
}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

URLS_WITHOUT_LANGUAGE_REDIRECT = ('/sitemap.xml',
                                  '/robots.xml',
                                  '/humans.txt',
                                  '/favicon.ico',
                                  '/admin')

ZTEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n', 
                ]
        }
    }]

# Expiration time in seconds, one hour as default

# from django.conf import settings

# TIME_ZONE = settings.TIME_ZONE
# LOGGING_CONFIG = settings.LOGGING_CONFIG

URLS_WITHOUT_LANGUAGE_REDIRECT = ('/sitemap.xml','/robots.xml','/humans.txt', '/admin/')


MULTIUPLOADER_FILE_EXPIRATION_TIME = 3600

MULTIUPLOADER_FILES_FOLDER = 'multiuploader'


MULTIUPLOADER_FORMS_SETTINGS = {
    'default': {
        'FILE_TYPES': ['jpg', 'jpeg', 'png', 'txt', 'zip', 'rar', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'odt', 'ods', 'odp', 'rtf'],
        'CONTENT_TYPES': [
                'image/jpeg',
                'image/png',
                'text/plain',
                'application/zip',
                'application/x-rar-compressed',
                'application/octet-stream',
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/vnd.ms-excel',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'application/vnd.ms-powerpoint',
                'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                'application/vnd.oasis.opendocument.text',
                'application/vnd.oasis.opendocument.spreadsheet',
                'application/vnd.oasis.opendocument.presentation',
                'text/rtf',
        ],
        'MAX_FILE_SIZE': 10485760,
        'MAX_FILE_NUMBER': 5,
        'AUTO_UPLOAD': True
    },
    'images': {
        'FILE_TYPES': ['jpg', 'jpeg', 'png', 'gif', 'svg', 'bmp', 'tiff', 'ico'],
        'CONTENT_TYPES': [
            'image/gif',
            'image/jpeg',
            'image/pjpeg',
            'image/png',
            'image/svg+xml',
            'image/tiff',
            'image/vnd.microsoft.icon',
            'image/vnd.wap.wbmp',
        ],
        'MAX_FILE_SIZE': 10485760,
        'MAX_FILE_NUMBER': 5,
        'AUTO_UPLOAD': True
    },
    'video': {
        'FILE_TYPES': ['flv', 'mpg', 'mpeg', 'mp4' ,'avi', 'mkv', 'ogg', 'wmv', 'mov', 'webm'],
        'CONTENT_TYPES': [
            'video/mpeg',
            'video/mp4',
            'video/ogg',
            'video/quicktime',
            'video/webm',
            'video/x-ms-wmv',
            'video/x-flv',
        ],
        'MAX_FILE_SIZE': 10485760,
        'MAX_FILE_NUMBER': 5,
        'AUTO_UPLOAD': True
    },
    'audio': {
        'FILE_TYPES': ['mp3', 'mp4', 'ogg', 'wma', 'wax', 'wav', 'webm'],
        'CONTENT_TYPES': [
            'audio/basic',
            'audio/L24',
            'audio/mp4',
            'audio/mpeg',
            'audio/ogg',
            'audio/vorbis',
            'audio/x-ms-wma',
            'audio/x-ms-wax',
            'audio/vnd.rn-realaudio',
            'audio/vnd.wave',
            'audio/webm'
        ],
        'MAX_FILE_SIZE': 10485760,
        'MAX_FILE_NUMBER': 5,
        'AUTO_UPLOAD': True
    },
}

MEETUP_API_KEY = '5971545d4317bf6936521750624c49'