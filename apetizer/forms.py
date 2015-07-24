'''
Created on 2 fevr. 2015

@author: nicolas
'''
from django.forms.models import ModelForm
from django.forms.forms import Form


class FormControlMixin(object):
    def set_form_control_class(self):
        for field_name in self.fields:
            self.fields[field_name].widget.attrs['class'] = 'form-control'


class BaseForm(FormControlMixin, Form):

    def __init__(self, *args, **kwargs):
        super(BaseForm, self).__init__(*args, **kwargs)
        self.set_form_control_class()


class BaseModelForm(FormControlMixin, ModelForm):

    def __init__(self, *args, **kwargs):
        super(BaseModelForm, self).__init__(*args, **kwargs)
        self.set_form_control_class()


class ActionPipeForm(BaseForm):
    slug = 'slug'
    title = ''
    hidden_fields = tuple()
    
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


class ActionModelForm(BaseModelForm):
    """
    Base dashboard form
    All forms in dashboard should inherit from it.
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