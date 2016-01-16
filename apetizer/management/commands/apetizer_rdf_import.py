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
from rdflib.namespace import RDF,RDFS,OWL



class Command(BaseCommand):
    help = ''


    def handle(self, *args, **options):
        
        
        g = Graph()


        g.parse("http://www.w3.org/1999/02/22-rdf-syntax-ns", format="n3")
        g.parse("http://www.w3.org/2000/01/rdf-schema", format="n3")
        g.parse("http://www.w3.org/2002/07/owl", format="n3")
        g.parse("http://xmlns.com/foaf/spec/20140114.rdf")

        print g.serialize( format='json-ld')
