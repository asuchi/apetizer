'''
Created on 5 fevr. 2016

@author: biodigitals
'''
from django.core.management.base import BaseCommand
from django.core.serializers import serialize

from apetizer.models import Item, Translation, Moderation, Visitor, DataPath


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def add_arguments(self, parser):
        parser.add_argument('root_slug', type=str)

    def handle(self, *args, **options):
        
        # get a list of all items in a root
        root_slug = options['root_slug']
        root_node = Item.objects.get_at_url('//'+root_slug+'/')
        
        nodes = root_node.get_descendants()
        nodes_uids = list(nodes.values_list('id', flat=True).order_by('id'))
        nodes_uids.append(root_node.id)
        
        # for each node get all dependencies
        translations = Translation.objects.filter(related_id__in=nodes_uids)
        moderations = Moderation.objects.filter(related_id__in=nodes_uids)
        
        # from all moderations, all translations, get all akeys involved
        akeys_uids = [root_node.akey]
        for qsv in (moderations.values_list('akey', flat=True), translations.values_list('akey', flat=True), nodes.values_list('akey', flat=True)):
            for key in qsv:
                if not key in akeys_uids:
                    akeys_uids.append(key)
        
        visitors = Visitor.objects.filter(akey__in=akeys_uids)
        datapaths = DataPath.objects.filter(akey__in=akeys_uids)
        
        # merge results by removing datapaths ids from
        model_result = []
        for results in (datapaths, visitors, moderations, translations, (root_node,), nodes):
            for result in results:
                model_result.append(result)
        
        model_data = serialize("json", model_result)
        
        file = open(root_slug+'.json', "w")
        file.write(model_data)
        file.close()
        
        

