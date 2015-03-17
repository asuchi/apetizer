from distutils.core import setup

setup(
    name='Apetizer',
    version='0.3.0',
    author='Nicolas Danjean',
    author_email='nicolas@biodigitals.com',
    packages=['apetizer',
              'apetizer.models',
              'apetizer.forms',
              'apetizer.parsers',
              'apetizer.storages',
              'apetizer.views',
              'apetizer.templatetags', 
              'apetizer.test'],
    scripts=[],
    url='http://github.com/biodigitals/apetizer/',
    license='LICENSE.txt',
    description='Django views for http, api and action scenarios.',
    long_description=open('README.md').read(),
    install_requires=[
        "Django >= 1.5",
    ],
)