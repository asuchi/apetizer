'''
Created on 27 janv. 2014

@author: rux
'''
import random
import re

from django.core.validators import EMPTY_VALUES
from django.db import models
from django.db.models import fields
from django.forms import ValidationError
from django.forms.widgets import TextInput
from django.utils.encoding import smart_unicode


class UIDField(models.CharField):
    """
    A field which stores a unique ID value, a 7 character random string made up of the
    lowercase english alphabet and numbers, minus ``o``,``i``,``1``, and ``0`` to avoid
    confusion. This may also have the Boolean attribute 'auto' which will set the value 
    on initial save to a new UID value (calculated using the random.choice method). 
    Note that while all UIDs are expected to be unique we enforce this with a DB constraint.
    """                                                                                     
    # Modified from http://www.davidcramer.net/code/420/improved-uuidfield-in-django.html   
    __metaclass__ = models.SubfieldBase                                                     

    def __init__(self, *args, **kwargs):
        auto = kwargs.pop('auto', False)

        if kwargs.get('primary_key', False):                                                
            assert auto, "Must pass auto=True when using UIDField as primary key."         
                                                             
        # Set this as a fixed value, we store UIDs in text.
        kwargs['max_length'] = kwargs.get('max_length', 7)
        
        if auto:
            # Do not let the user edit UIDs if they are auto-assigned.
            kwargs['editable'] = False
            kwargs['blank'] = True
            kwargs['unique'] = True
        
        self.auto = auto
        
        super(UIDField, self).__init__(*args, **kwargs)

    def gen_value(self):
        return ''.join(random.choice('abcdefghjkmnpqrstuvwxyz23456789')
                       for i in xrange(self.max_length)) #@UnusedVariable
    
    def pre_save(self, model_instance, add):
        """Ensures that we auto-set values if required. See CharField.pre_save."""          
        value = getattr(model_instance, self.attname, None)                                 
        if not value and self.auto:                                                         
            # Assign a new value for this attribute if required.
            # Note that the list of values here excludes o,i,0,1 for easy typing
            value = self.gen_value()
            setattr(model_instance, self.attname, value)
            
            queryset = model_instance.__class__.objects.all()
            
            # Check for collision and try again
            ex_filter = "%s__exact" % self.attname
            while queryset.filter(**{ex_filter: value}):
                value = self.gen_value()
                
        return value
        
    def to_python(self, value):
        if not value:
            return None                                              
        assert len(value) == self.max_length
        return value

try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ["^content\.fields\.UIDField"])
except:
    pass



#from django.forms import fields
class IntegerRangeField(models.IntegerField):
    def __init__(self, verbose_name=None, name=None, min_value=None, max_value=None, **kwargs):
        self.min_value, self.max_value = min_value, max_value
        models.IntegerField.__init__(self, verbose_name, name, **kwargs)
    def formfield(self, **kwargs):
        defaults = {'min_value': self.min_value, 'max_value':self.max_value}
        defaults.update(kwargs)
        return super(IntegerRangeField, self).formfield(**defaults)

try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ["^content\.fields\.IntegerRangeField"])
except:
    pass



class HexColorField(fields.Field):
    
    default_error_messages = {
        'hex_error': u'This is an invalid color code. It must be a html hex color code e.g. #000000'
    }
    
    def clean(self, value):
        
        super(HexColorField, self).clean(value)
        
        if value in EMPTY_VALUES:
            return u''
        
        value = smart_unicode(value)
        value_length = len(value)
        
        if value_length != 7 or not re.match('^\#([a-fA-F0-9]{6}|[a-fA-F0-9]{3})$', value):
            raise ValidationError(self.error_messages['hex_error'])
        
        return value

    def widget_attrs(self, widget):
        if isinstance(widget, (TextInput)):
            return {'maxlength': str(7)}

try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ["^content\.fields\.HexColorField"])
except:
    pass
