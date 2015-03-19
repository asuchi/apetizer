'''
Created on 3 fevr. 2015

@author: nicolas
'''
from django.forms import fields, widgets
from django.forms.widgets import HiddenInput
from django.utils.translation import ugettext_lazy as _
from parsley.decorators import parsleyfy

from apetizer.forms.actionpipe import ActionPipeForm


@parsleyfy
class RegisterOrLoginForm(ActionPipeForm):
    """ Basic form to get user email and check if we know him """
    slug = 'register-login-form'

    email = fields.EmailField(label=_('Your email address'), widget=fields.TextInput(attrs={'placeholder': _(u'your@email.com')}))

@parsleyfy
class RegisterLoginForm(ActionPipeForm):
    """ Basic login form """
    slug = 'register-login-form'

    email = fields.EmailField(label=_('Your email address'), widget=fields.TextInput(attrs={'placeholder': _(u'your@email.com')}))
    password = fields.CharField(label=_('Your password'), required=False, widget=widgets.PasswordInput)

@parsleyfy
class LoginInfosForm(ActionPipeForm):
    """ Basic form to collect sigining up user's login infos """
    slug = 'login-form'
    title = _("Your login informations")
    
    email = fields.EmailField(label=_(u'Email'), widget=fields.TextInput(attrs={'placeholder': _(u'your@email.com')}))
    password = fields.CharField(label=_(u'Password'), widget=widgets.PasswordInput)

@parsleyfy
class RegisterInfosForm(ActionPipeForm):
    """ Basic registration form """
    slug = 'personnal-infos-form'
    title = _("Your contact informations")

    first_name = fields.CharField(label=_(u'First name'), widget=fields.TextInput(attrs={'placeholder': _(u'First name')}))
    last_name = fields.CharField(label=_(u'Last name'), 
                                         help_text=_(u"This information will not be public"),
                                         widget=fields.TextInput(attrs={'placeholder': _(u'Last name')}))
    
    terms_agreed_p = fields.BooleanField(label=_('Accepts terms and conditions'), required=True, initial=True, widget=HiddenInput())
    
    hidden_fields = ['terms_agreed_p',]

@parsleyfy
class RegisterCompleteForm(ActionPipeForm):
    """ Basic form when asking user to complete his profile """
    slug = 'personnal-infos-form'

    first_name = fields.CharField(label=_(u'First name'), widget=fields.TextInput(attrs={'placeholder': _(u'First name')}))
    last_name = fields.CharField(label=_(u'Last name'), 
                                         help_text=_(u"Only your last name initial will be public"), 
                                         widget=fields.TextInput(attrs={'placeholder': _(u'Last name')}))
    