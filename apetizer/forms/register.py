'''
Created on 3 fevr. 2015

@author: nicolas
'''
from django.contrib.auth.models import User
from django.forms import fields, widgets, TextInput
from django.utils.translation import ugettext_lazy as _

from apetizer.forms.base import ActionPipeForm, ActionModelForm
from apetizer.models import Visitor


class RegisterOrLoginForm(ActionPipeForm):
    """ Basic form to get user email and check if we know him """
    slug = 'register-login-form'

    email = fields.EmailField(label=_('Your email address'),
                              widget=TextInput(attrs={'placeholder':
                                                             _(u'your@email.com')}
                                                      ))

class AuthenticateLoginForm(ActionPipeForm):
    """ Basic form to collect sigining up user's login infos """
    slug = 'login-form'
    title = _("Your login informations")
    
    username = fields.CharField(label=_(u'Identifiant'),
                              widget=TextInput(attrs={'placeholder':
                                                             _(u'identifiant')}
                                                      ))
    
    password = fields.CharField(label=_(u'Password'),
                                widget=widgets.PasswordInput)


class AuthenticateLostForm(ActionPipeForm):
    """ Basic form to collect sigining up user's login infos """
    slug = 'login-form'
    title = _("Your login informations")
    
    lost_email = fields.EmailField(label=_(u'Email'),
                              widget=TextInput(attrs={'placeholder':
                                                             _(u'your@email.com')}
                                                      ))


class AuthenticatePasswordForm(ActionPipeForm):
    slug = 'register-password-form'
    title = _("Set a password")

    password = fields.CharField(label=_('Your password'), required=True,
                                widget=widgets.PasswordInput)




class AuthenticateAgreeForm(ActionPipeForm):
    slug = 'register-agree-form'
    title = _("Agree terms and conditions ?")

    terms_agreed = fields.BooleanField(label=_('Agree terms and conditions ?'),
                                         required=True, initial=False,
                                         )


class RegisterForm(ActionPipeForm):
    """ Basic registration form """
    slug = 'register-infos-form'
    title = _("What's your name ?")

    username = fields.CharField(label=_(u'Your name'),
                            required=True,
                                  widget=TextInput(attrs={'placeholder':
                                                                 _(u'...')
                                                                 }
                                                          ))
    
    email = fields.EmailField(label=_('Your email address'),
                              required=True,
                              widget=TextInput(attrs={'placeholder':
                                                         _(u'your@email.com')
                                                         }
                                                      ))

class VisitorForm(ActionModelForm):
    class Meta:
        fields = ('username', 'email')
        model = Visitor

class VisitorValidateForm(ActionPipeForm):
    slug = 'register-validate-form'
    title = _("Copy paste the key you received to validate your email")

    token = fields.CharField(label=_(u'Clef'),
                                 widget=TextInput(attrs={'placeholder':
                                                                _(u'xxxxxxxxxxxx')}
                                                         ))

class VisitorPrivatizeForm(ActionPipeForm):
    slug = 'register-privatize-form'
    title = _("Copy paste the key you received to validate your email")

    policy = fields.CharField(label=_(u'Privacy policy'),
                                 widget=TextInput(attrs={'placeholder':
                                                                _(u'xxxxxxxxxxxx')}
                                                         ))


class UserForm(ActionModelForm):
    
    class Meta:
        fields = ('first_name', 'last_name',)
        model = User
    
    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True

    def save(self):
        return False