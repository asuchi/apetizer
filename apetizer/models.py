'''
Created on Feb 11, 2015

@author: nicolas
'''
from django.db import models


class AbstractPipeModel(models.Model):
    """
    An abstract base model for forms without model
    """
    class Meta:
        abstract = True


class AuditedModel(models.Model):
    '''
    Abstract Model that adds in audit / UID fields.
    
    Note that since this is abstract the UID is not globally unique; it is unique
    only for the concrete model where it is used (and on any children)
    '''
    uid = UIDField(_('uid'), auto=True)
    created_by = models.ForeignKey(User, blank=True, null=True, related_name='%(class)s_creator')
    created_date = models.DateTimeField(_('created on'), editable=False)
    modified_by = models.ForeignKey(User, blank=True, null=True, related_name='%(class)s_modifier')
    modified_date = models.DateTimeField(_('modified on'), editable=False)
    
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # Some child implementations (like VersionedModel) want to persist the created_date
        # of the oldest ancestor.  This check thus allows that.
        now_dtz = now()
        if not self.id and not self.created_date:
            self.created_date = now_dtz
        self.modified_date = now_dtz
        super(AuditedModel, self).save(*args, **kwargs)

    def can_be_modified_by_user(self, user):
        '''
        Whether this model can be modified by a given user. This is used by
        the `modify_by_user` method, and by default it just returns True. Any
        subclasses should override this if they want specific permission checks.
        '''
        return True

