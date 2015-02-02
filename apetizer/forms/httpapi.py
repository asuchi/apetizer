'''
Created on 9 sept. 2014

@author: rux
'''
from django.forms.models import ModelForm
from parsley.decorators import parsleyfy


@parsleyfy
class HttpApiForm(ModelForm):
    """
    Base dashboard form
    All forms in dashboard should inherit from it.
    Will automatically add parsley validation.
    """
    is_saved = False
    def get_instance(self):

        return self.instance

    def get_data(self):
        
        data = {}
        for field_name in self.fields:
            value = self[field_name].value()
            if value == None:
                value = self._raw_value(field_name)
            data[field_name] = value

        return data

