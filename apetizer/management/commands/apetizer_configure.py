'''
Created on 19 oct. 2015

@author: biodigitals
'''
import uuid

from django.core.management.base import BaseCommand
from apetizer.models import Frontend

class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def handle(self, *args, **options):
        
        # create a default root
        kwargs = {}
        akey = str(uuid.uuid4())
        kwargs['pipe'] = {'akey':akey,
                          'action':'doc',
                          'path':'/',
                          'locale':'fr',
                          'status':'added',
                          }
        # create the default host if not exists
        
        # create the argument host
        frontend = Frontend()
        
        #
        