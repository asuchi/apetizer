'''
Created on 3 fevr. 2015

@author: nicolas
'''
from django.forms import fields, widgets
from django.utils.translation import ugettext_lazy as _

from apetizer.forms.actionpipe import ActionPipeForm


class LoginInfosForm(ActionPipeForm):
    """ Basic form to collect sigining up user's login infos """
    slug = 'login-form'
    title = _("Your login informations")
    
    email = fields.EmailField(label=_(u'Email'),
                              widget=fields.TextInput(attrs={'placeholder':
                                                             _(u'your@email.com')}
                                                      ))
    
    password = fields.CharField(label=_(u'Password'),
                                widget=widgets.PasswordInput)


class RegisterOrLoginForm(ActionPipeForm):
    """ Basic form to get user email and check if we know him """
    slug = 'register-login-form'

    email = fields.EmailField(label=_('Your email address'),
                              widget=fields.TextInput(attrs={'placeholder':
                                                             _(u'your@email.com')}
                                                      ))


class RegisterLoginForm(ActionPipeForm):
    """ Basic login form """
    slug = 'register-login-form'

    email = fields.EmailField(label=_('Your email address'),
                              widget=fields.TextInput(attrs={'placeholder':
                                                             _(u'your@email.com')
                                                             }
                                                      ))

    password = fields.CharField(label=_('Your password'), required=False,
                                widget=widgets.PasswordInput)




class RegisterInfosForm(ActionPipeForm):
    """ Basic registration form """
    slug = 'register-infos-form'
    title = _("Your contact informations")

    first_name = fields.CharField(label=_(u'First name'),
                                  widget=fields.TextInput(attrs={'placeholder':
                                                                 _(u'First name')
                                                                 }
                                                          ))
    last_name = fields.CharField(label=_(u'Last name'),
                                 widget=fields.TextInput(attrs={'placeholder':
                                                                _(u'Last name')}
                                                         ))

class RegisterAgreeForm(ActionPipeForm):
    slug = 'register-agree-form'
    title = _("Agree terms and conditions")

    terms_agreed = fields.BooleanField(label=_('Accepts terms and conditions'),
                                         required=True, initial=True,
                                         )


class RegisterCompleteForm(ActionPipeForm):
    """ Basic form when asking user to complete his profile """
    slug = 'register-complete-form'


