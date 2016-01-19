'''
Created on 16 juil. 2015

@author: biodigitals
'''
from django.forms.fields import CharField, TypedChoiceField, NullBooleanField, \
    IntegerField
from django.forms.widgets import Textarea, TextInput, RadioSelect
from django.utils.translation import ugettext_lazy as _

from apetizer.forms.base import ActionPipeForm, ActionModelForm
from apetizer.models import Moderation


class ModerateInviteForm(ActionPipeForm):
    emails = CharField(max_length=1024, widget=Textarea)
    subject = CharField(max_length=185)
    message = CharField(max_length=4096, widget=Textarea)
    
class ModerateEvaluateForm(ActionPipeForm):
    score = IntegerField(initial=0,min_value=0,max_value=5)
    status = CharField(max_length=65)
    subject = CharField(max_length=185)
    message = CharField(max_length=4096, widget=Textarea)

class ModerateProposeForm(ActionPipeForm):
    subject = CharField(max_length=185)
    message = CharField(max_length=4096, widget=Textarea)

class ModerateSubscribeForm(ActionPipeForm):
    subscribe = NullBooleanField(initial=False)


class ModerateCommentForm(ActionModelForm):
    subject = CharField(max_length=65, required=False)
    message = CharField(max_length=4096, widget=Textarea)
    class Meta:
        model = Moderation
        fields = ('subject', 'message',)
    
    def save(self, *args, **kwargs):
        self.instance.status = 'comment'
        self.full_clean()
        if not self.instance.subject:
            self.instance.subject = 'Commentaire'
        super(ModerateCommentForm, self).save(*args, **kwargs)

class ModerateDiscussForm(ActionModelForm):
    message = CharField(max_length=4096, widget=Textarea)
    class Meta:
        model = Moderation
        fields = ('message',)
    
    def save(self, *args, **kwargs):
        self.instance.status = 'told'
        self.full_clean()
        if not self.instance.subject:
            self.instance.subject = 'Told ...'
        super(ModerateDiscussForm, self).save(*args, **kwargs)

class ModerateContactForm(ActionModelForm):
    subject = CharField(max_length=156)
    message = CharField(max_length=4096, widget=Textarea, required=True)
    
    class Meta:
        model = Moderation
        fields = fields = ('subject', 'message')
    
    def save(self, *args, **kwargs):
        
        self.instance.status = 'contact'
        self.full_clean()
        
        super(ModerateContactForm, self).save(*args, **kwargs)



class ModerateReviewForm(ActionModelForm):
    status = CharField(max_length=65)
    subject = CharField(max_length=185, required=False)
    message = CharField(max_length=4096, widget=Textarea, required=False)
    
    class Meta:
        model = Moderation
        fields = ('status', 'subject', 'message')
    
    def save(self, *args, **kwargs):
        
        self.full_clean()
        
        if not self.instance.subject:
            self.instance.subject = 'Revue'
        if not self.instance.message:
            self.instance.message = 'Nouvel avis "'+self.cleaned_data['status']+'" de '+self.instance.get_full_name()
        
        super(ModerateReviewForm, self).save(*args, **kwargs)

class AModerateContactForm(ActionPipeForm):
    
    subject = CharField(label=_(u'Subject'),
                                 widget=TextInput(attrs={'placeholder':
                                                                _(u'what is it about ?')}
                                                         ))

    message = CharField(label=_(u'Message'),
                                 widget=Textarea(attrs={'placeholder':
                                                                _(u'Message')}
                                                         ))


class AModerateSubscribeForm(ActionPipeForm):
    
    subscribe = TypedChoiceField(label=_('Keep me informed !'),
                                  required=True, initial='Yes',
                                  coerce=lambda x: x == 'Yes',
                                  choices=((True, 'Yes'),(False, 'No')),
                                  widget=RadioSelect
                                  )

