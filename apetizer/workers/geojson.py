'''
Created on 16 oct. 2015

@author: biodigitals
'''
import json

from apetizer.models import Item


def import_data(self, user_profile, **kwargs):
    
    sample = {u'geometry': {u'type': u'Point', u'coordinates': [u'-1.74779', u'47.52253']}, u'type': u'Feature', u'properties': {u'description': u"Journ\xe9e de partage et de mobilisation sur le th\xe8me de l'alimentation raisonn\xe9e et responsable. Conf\xe9rences, projections, ateliers cuisine v\xe9g\xe9tarienne, producteurs locaux.", u'theme': u'Se nourrir / Faire soi-m\xeame / Recycler / Se soigner...', u'id': u'167', u'name': u'"DU BIEN-ETRE DANS NOS ASSIETTES"'}}
    
    # load the json file as projets
    projets = {}
    projets['features'] = [sample]
    
    projets = json.loads(file('/Users/biodigitals/Desktop/Datasources/carto-colibris-projets.json.txt', 'ra').readlines()[0])
    
    for projet in projets['features']:
        
         project_url = kwargs['node'].get_path()+'/'+projet['properties']['theme'].split(' / ')[0]
         
         item = Item.objects.get_or_create_url(project_url+'/'+str(projet['properties']['id']), **kwargs)
         
         item.path = project_url
         
         item.action = 'import'
         item.locale = 'fr'
         
         item.akey = user_profile.akey
         item.username = user_profile.username
         
         item.subject = 'Import'
         item.message = 'Data Imported'
         
         #item.longitude = projet['geometry']['coordinates'][0]
         #item.latitude = projet['geometry']['coordinates'][1]
         
         item.label = projet['properties']['theme'].split(' / ')[-1]
         item.title = projet['properties']['name']
         item.description = projet['properties']['description']
         
         del projet['properties']
         
         item.geodata = json.dumps(projet)
         
         item.full_clean()
         item.save()


# register the service plugin

