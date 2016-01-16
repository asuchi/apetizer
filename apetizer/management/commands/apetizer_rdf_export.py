'''
Created on 13 jan. 2016

@author: sebastator
'''
import inspect
import os
import uuid

from django.core.management.base import BaseCommand, CommandError
from django.utils.html import escape
from django.forms.models import model_to_dict
from apetizer.models import Item, Moderation, get_distincts
from apetizer.views.front import FrontView


from rdflib import Graph, plugin
from rdflib.serializer import Serializer
import json,datetime

json_item="""
{
  "@context": [
                "https://schema.org/"
                ],
  "@id": "%s",
  "@type": "%s",
   %s
}
"""



empty_json_item="""
{
  "@context": [
                "https://schema.org/"
                ],
  "@id": "%s",
  "@type": "%s"
}
"""


class Command(BaseCommand):
    help = ''


    def handle(self, *args, **options):
        
        g = Graph()

        for elt in Item.objects.all():

            elt_type=elt.type
            uri="http://localhost"+elt.get_uid_url()

            data=dict()

            for k,v in model_to_dict(elt).items():
                elt_type = type(v).__name__

                if elt_type == "datetime":
                    pass#data[k]=v
                elif elt_type =="FieldFile":
                    pass#data[k]=v
                elif elt_type =="ImageFieldFile":
                    pass#data[k]=v
                elif elt_type =="NoneType":
                    pass#data[k]=v
                else:
                    data[k]=v


            elt_data=json.dumps(data)

            data=json_item%(uri,elt_type,elt_data[1:-1])
                
            g.parse(data=data,format='json-ld')


        for s,p,o in g:
            print s,p,o

