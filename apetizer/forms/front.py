'''
Created on 17 mars 2015

@author: rux
'''
from django.forms.fields import EmailField, CharField
from django.forms.widgets import TextInput, PasswordInput
from django.utils.translation import ugettext as _

from apetizer.forms.httpapi import HttpApiForm


class LoginForm(HttpApiForm):
    """ Basic login form """
    slug = 'login'
    
    email = EmailField(label=_('Your email address'), widget=TextInput(attrs={'placeholder': _(u'your@email.com')}))
    password = CharField(label=_('Your password'), required=False, widget=PasswordInput)