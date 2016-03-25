'''
Created on Feb 19, 2015

@author: nicolas
'''
import mimetypes
import os
import re

from django import forms
from django.conf import settings
from django.forms.fields import BooleanField, FloatField, DateTimeField
from django.forms.widgets import Textarea
from django.utils.html import mark_safe
from django.utils.translation import ugettext_lazy as _

import apetizer.settings as DEFAULTS
from apetizer.forms.base import ActionModelForm
from apetizer.forms.base import ActionPipeForm
from apetizer.models import Item, Translation, DATETIME_FORMATS
from apetizer.parsers.api_json import dump_json
from apetizer.utils.upload import format_file_extensions


class FormControlMixin(object):
    def set_form_control_class(self):
        for field_name in self.fields:
            self.fields[field_name].widget.attrs['class'] = 'form-control'


class BaseForm(FormControlMixin, ActionPipeForm):

    def __init__(self, *args, **kwargs):
        super(BaseForm, self).__init__(*args, **kwargs)
        self.set_form_control_class()


class BaseModelForm(FormControlMixin, ActionModelForm):

    def __init__(self, *args, **kwargs):
        super(BaseModelForm, self).__init__(*args, **kwargs)
        self.set_form_control_class()

class ItemAddForm(ActionModelForm):
    class Meta:
        model = Item
        fields = ('label', 'title', 'description','order')


class ItemReorderForm(ActionModelForm):
    class Meta:
        model = Item
        fields = ('order',)

class ItemTranslateForm(ActionModelForm):
    slug = 'item_translate'
    title = _('Translate this item')
    class Meta:
        model = Translation
        fields = ('label', 'title', 'description')

class ItemRenameForm(ActionModelForm):
    slug = 'item_rename'
    title = _('Rename this item')
    class Meta:
        model = Translation
        fields = ('slug',)

class ItemChangeForm(ActionModelForm):
    class Meta:
        model = Item
        fields = ('behavior', 'order',)

class ItemImageForm(ActionModelForm):
    slug = 'item_image'
    title = _('Modify this item')
    class Meta:
        model = Item
        fields = ('image',)

class ItemFileForm(ActionModelForm):
    slug = 'item_file'
    title = _('Modify this item')
    class Meta:
        model = Item
        fields = ('file',)

class ItemCodeForm(ActionModelForm):
    slug = 'item_code'
    title = _('Code for this item')
    class Meta:
        model = Translation
        fields = ('content',)

class ItemPublishForm(ActionModelForm):
    class Meta:
        model = Item
        fields = ('behavior', 'type', 'published')

class ItemDataForm(ActionModelForm):
    slug = 'item_data'
    title = _('Code for this item')
    data = forms.CharField(max_length=4096, widget=Textarea(attrs={'cols':10,'rows':40}))
    
    class Meta:
        model = Item
        fields = ('data',)
    
class ItemRedirectForm(ActionModelForm):
    slug = 'item_redirect'
    title = _('Code for this item')
    class Meta:
        model = Translation
        fields = ('redirect_url',)

class ItemLocationForm(ActionModelForm):
    slug = 'item_location'
    title = _('Locate this item')
    
    latitude = FloatField(required=False)
    longitude = FloatField(required=False)

    class Meta:
        model = Item
        fields = ('latitude', 'longitude')

class ItemTimingForm(ActionModelForm):
    slug = 'item_timing'
    title = _('Timing for this item')
    
    start = DateTimeField(input_formats=DATETIME_FORMATS,)
    end = DateTimeField(input_formats=DATETIME_FORMATS,required=False)
    
    class Meta:
        model = Item
        fields = ('start', 'end')


class ItemDeleteForm(ActionModelForm):
    slug = 'item_delete'
    title = _('Delete this item')
    do_delete = BooleanField(
        label=_(u'Yes, delete this object'),
        required=True,
    )
    class Meta:
        model = Item
        fields = tuple()


class ItemRelatedForm(ActionModelForm):
    slug = 'item_related'
    title = _('Related for this item')
    class Meta:
        model = Item
        fields = ('related_url', 'related_cron')



class MultiuploadWidget(forms.MultipleHiddenInput):
    def __init__(self, attrs={}):
        super(MultiuploadWidget, self).__init__(attrs)

    def render(self, name, value, attrs=None):
        widget_ = super(MultiuploadWidget, self).render(name, value, attrs)
        output = '<div id="hidden_container" style="display:none;">%s</div>' % widget_
        return mark_safe(output)


class MultiuploaderField(forms.MultiValueField):
    widget = MultiuploadWidget()

    def formfield(self, **kwargs):
        kwargs['widget'] = MultiuploadWidget
        return super(MultiuploaderField, self).formfield(**kwargs)

    def validate(self, values):
        super(MultiuploaderField, self).validate(values)

    def clean(self, values):
        super(MultiuploaderField, self).clean(values)
        return values

    def compress(self, value):
        if value:
            return value

        return None


class MultiUploadForm(forms.Form):
    file = forms.FileField()

    def __init__(self, *args, **kwargs):
        multiuploader_settings = getattr(settings, "MULTIUPLOADER_FORMS_SETTINGS", DEFAULTS.MULTIUPLOADER_FORMS_SETTINGS)

        form_type = kwargs.pop("form_type", "default")

        options = {
            'maxFileSize': multiuploader_settings[form_type]["MAX_FILE_SIZE"],
            'acceptFileTypes': format_file_extensions(multiuploader_settings[form_type]["FILE_TYPES"]),
            'maxNumberOfFiles': multiuploader_settings[form_type]["MAX_FILE_NUMBER"],
            'allowedContentTypes': list(map(str.lower, multiuploader_settings[form_type]["CONTENT_TYPES"])),
            'autoUpload': multiuploader_settings[form_type]["AUTO_UPLOAD"]
        }

        self._options = options
        self.options = dump_json(options)

        super(MultiUploadForm, self).__init__(*args, **kwargs)

        self.fields["file"].widget = forms.FileInput(attrs={'multiple': True})

    def clean_file(self):
        content = self.cleaned_data[u'file']

        filename, extension = os.path.splitext(content.name)

        if re.match(self._options['acceptFileTypes'], extension, flags=re.I) is None:
            raise forms.ValidationError('acceptFileTypes')
        
        try:
            import magic
            content_type = magic.from_buffer(content.read(1024), mime=True)
        except:
            # guess content type from extension
            content_type = mimetypes.guess_type(content.name)[0]
            
        if content_type.lower() in self._options['allowedContentTypes']:
            if content._size > self._options['maxFileSize']:
                raise forms.ValidationError("maxFileSize")
        else:
            raise forms.ValidationError("acceptFileTypes")

        return content


class MultiuploaderMultiDeleteForm(forms.Form):
    id = MultiuploaderField()

