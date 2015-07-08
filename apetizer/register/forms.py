'''
Created on 3 fevr. 2015

@author: nicolas
'''
from django.forms import fields, widgets, Textarea, TextInput
from django.utils.translation import ugettext_lazy as _

from apetizer.forms.actionpipe import ActionPipeForm
from django.forms.widgets import HiddenInput


class LoginForm(ActionPipeForm):
    """ Basic form to collect sigining up user's login infos """
    slug = 'login-form'
    title = _("Your login informations")
    
    email = fields.EmailField(label=_(u'Email'),
                              widget=TextInput(attrs={'placeholder':
                                                             _(u'your@email.com')}
                                                      ))
    
    password = fields.CharField(label=_(u'Password'),
                                widget=widgets.PasswordInput)


class RegisterOrLoginForm(ActionPipeForm):
    """ Basic form to get user email and check if we know him """
    slug = 'register-login-form'

    email = fields.EmailField(label=_('Your email address'),
                              widget=TextInput(attrs={'placeholder':
                                                             _(u'your@email.com')}
                                                      ))


class RegisterLoginForm(ActionPipeForm):
    """ Basic login form """
    slug = 'register-login-form'

    email = fields.EmailField(label=_('Your email address'),
                              widget=TextInput(attrs={'placeholder':
                                                             _(u'your@email.com')
                                                             }
                                                      ))

    password = fields.CharField(label=_('Your password'), required=False,
                                widget=widgets.PasswordInput)




class RegisterForm(ActionPipeForm):
    """ Basic registration form """
    slug = 'register-infos-form'
    title = _("Your contact informations")

    first_name = fields.CharField(label=_(u'First name'),
                                  widget=TextInput(attrs={'placeholder':
                                                                 _(u'First name')
                                                                 }
                                                          ))
    last_name = fields.CharField(label=_(u'Last name'),
                                 widget=TextInput(attrs={'placeholder':
                                                                _(u'Last name')}
                                                         ))



class RegisterAgreeForm(ActionPipeForm):
    slug = 'register-agree-form'
    title = _("Agree terms and conditions")

    terms_agreed = fields.BooleanField(label=_('Accepts terms and conditions'),
                                         required=True, initial=True,
                                         )

class RegisterContactForm(ActionPipeForm):
    slug = 'register-agree-form'
    title = _("Agree terms and conditions")
    
    objet = fields.CharField(label=_(u'Objet'),
                                 widget=TextInput(attrs={'placeholder':
                                                                _(u'what about ?')}
                                                         ))
    
    message = fields.CharField(label=_(u'Message'),
                                 widget=Textarea(attrs={'placeholder':
                                                                _(u'Message')}
                                                         ))


class RegisterSubscribeForm(ActionPipeForm):
    slug = 'register-subscribe-form'
    title = _("Subscribe to newsletter")
    
    email = fields.EmailField(label=_('Your email address'),
                              widget=TextInput(attrs={'placeholder':
                                                         _(u'your@email.com')
                                                         }
                                                      ))
    
    subscribe = fields.BooleanField(label=_('Yes, Keep me informed !'),
                                    required=True, initial=True)




