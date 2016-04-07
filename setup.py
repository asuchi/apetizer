from distutils.core import setup


setup(
    name='Apetizer',
    version='0.8',
    author='Nicolas Danjean',
    author_email='nicolas@biodigitals.com',
    packages=['apetizer',
              'apetizer.directory',
              'apetizer.forms',
              'apetizer.management',
              'apetizer.middleware',
              'apetizer.migrations',
              'apetizer.parsers',
              'apetizer.storages',
              'apetizer.templatetags',
              'apetizer.test',
              'apetizer.utils',
              'apetizer.views',
              ],
    package_data={'apetizer': ['apetizer/templates/*']},
    scripts=[],
    url='http://github.com/biodigitals/apetizer/',
    license='LICENSE.txt',
    description='Django views for http, api and action scenarios.',
    long_description=open('readme.txt').read(),
    install_requires=[
        "Pillow>=2.6.1",
        "python-magic>=0.4.6",
        "pytz>=2014.7",
        "python-twitter",
        "python-geohash",
        "geopy",
        "dateutils",
        "Django>=1.8.4",
        "django-markdown-deux",
        "six>=1.8.0",
        'django-jsonfield',
        'django-leaflet',
        'requests-oauthlib'
    ],
    entry_points = {
        'console_scripts': [
            'apetizer = manage:parse_command',                  
        ],              
    },
)