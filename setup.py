from distutils.core import setup


setup(
    name='Apetizer',
    version='0.5',
    author='Nicolas Danjean',
    author_email='nicolas@biodigitals.com',
    packages=['apetizer',
              'apetizer.dispatchers',
              'apetizer.forms',
              'apetizer.middleware',
              'apetizer.parsers',
              'apetizer.storages',
              'apetizer.templatetags',
              'apetizer.test',
              'apetizer.utils',
              'apetizer.views',
              'apetizer.workers',
              ],
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