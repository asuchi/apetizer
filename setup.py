from distutils.core import setup
import codecs

setup(
    name='Apetizer',
    version='0.3.1',
    author='Nicolas Danjean',
    author_email='nicolas@biodigitals.com',
    packages=['apetizer',
              'apetizer.forms',
              'apetizer.parsers',
              'apetizer.storages',
              'apetizer.views',
              'apetizer.templatetags',
              'apetizer.test'],
    package_data={'apetizer': ['apetizer/templates/*']},
    scripts=[],
    url='http://github.com/biodigitals/apetizer/',
    license='LICENSE.txt',
    description='Django views for http, api and action scenarios.',
    long_description=open('readme.txt').read(),
    install_requires=[
        "Django >= 1.5",
    ],
)