#
from apetizer.forms.base import ActionPipeForm
from django.forms import CharField

class ItemCutForm(ActionPipeForm):
    uid = CharField(label="item id to cut", max_length=185, required=True)

class ItemCopyForm(ActionPipeForm):
    uid = CharField(label="item id to copy", max_length=185, required=True)

class ItemPasteForm(ActionPipeForm):
    uid = CharField(label="item id to paste", max_length=185, required=True)