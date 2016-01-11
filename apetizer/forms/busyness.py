'''
Created on 20 nov. 2015

@author: biodigitals
'''
from apetizer.forms.base import ActionModelForm
from apetizer.models import Moderation


class ItemTranslateForm(ActionModelForm):
    slug = 'item_translate'
    title = _('Translate this item')
    class Meta:
        model = Moderation
        fields = ('cost', 'reward', 'status')
