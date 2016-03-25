import os
APPEND_SLASH = False
DEBUG = True
USE_TZ = True
ROOT_URLCONF = "project_name.urls"
SECRET_KEY = "fsldjkhgljkfshfgnlcuqsngfiu"
ALLOWED_HOSTS = [ "*"]
STATIC_ROOT = "static"
STATIC_URL = "/static/"
MEDIA_ROOT = "media"
MEDIA_URL = "/media/"
INSTALLED_APPS = ( 
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "django.contrib.sessions",
    "django.contrib.sitemaps",
    "leaflet",
    "apetizer",
    "project_name",
    )

MIDDLEWARE_CLASSES = (
    #"apetizer.middleware.BasicAuthMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "apetizer.middleware.multilingual.EnforcedMultilingualURLMiddleware",
)

WSGI_APPLICATION = "wsgi.application"
DATABASES = {
    'default':{
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'test.db',
     },
}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

URLS_WITHOUT_LANGUAGE_REDIRECT = ('/sitemap.xml','/robots.xml','/humans.txt')

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
