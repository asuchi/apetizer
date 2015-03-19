'''
Created on 9 sept. 2014

@author: rux
'''
from django.forms.models import ModelForm


class HttpApiForm(ModelForm):
    """
    Base dashboard form
    All forms in dashboard should inherit from it.
    Will automatically add parsley validation.
    """
    is_saved = False

    def get_data(self):
        """
        Get the form fields data as dict
        """
        data = {}
        for field_name in self.fields:
            value = self[field_name].value()
            if value is None:
                value = self._raw_value(field_name)
            data[field_name] = value

        return data
