'''
Created on 15 janv. 2013

@author: rux
'''
from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import AdminFileWidget
from django.contrib.sites.admin import SiteAdmin
from django.core.urlresolvers import reverse
from django.forms.models import ModelForm

from apetizer import models
from apetizer.models import Item, Translation, \
                            Visitor, Moderation


class FrontendAdmin(SiteAdmin):
    list_display = SiteAdmin.list_display + ('subdomains','published')
admin.site.register(models.Frontend, FrontendAdmin)

def current_url(obj):
    return obj.get_url()

def current_label(obj):
    return obj.label

def current_slug(obj):
    return obj.slug

def current_title(obj):
    return obj.title

class DataPathAdmin(admin.ModelAdmin):
    model = models.DataPath
    list_display = ('action', 'akey', 'path', 'locale',  'data', 'ref_time', 'created_date', 'modified_date', 'completed_date', 'visible')
    ordering = ('-ref_time',)
admin.site.register(models.DataPath, DataPathAdmin)


class VisitorAdminForm(ModelForm):
    class Meta:
        model = Visitor
        exclude = ()

class VisitorAdmin(admin.ModelAdmin):
    model = Visitor
    form = VisitorAdminForm
    list_display = ('ref_time', 'path', 'akey', 'email', 'username', 'validated', )
    readonly_fields = ('akey', 'validated')
    ordering = ('-ref_time',)

admin.site.register(Visitor, VisitorAdmin)


class ModerationAdmin(admin.ModelAdmin):
    list_filter = ['validated', 'status',]
    list_display = ('ref_time', 'akey', 'email', 'related', 'status', 
                    'message', 'validated', 'subscribed', 'is_sent', 'data')
    ordering = ('-ref_time',)
    readonly_fields = ('related', 'origin')

admin.site.register(Moderation, ModerationAdmin)



def key_slug(obj):
    return obj.related.slug

class ItemForm(ModelForm):
    class Meta:
        model = Item
        exclude = ('created_by', 'modified_by', )

class TranslationForm(ModelForm):
    class Meta:
        model = Translation
        exclude = ('created_by', 'modified_by', )


#class TranslationInline(admin.StackedInline):
#    model = models.Translation
#    extra = 1
#    min_num = 1

class ItemAdmin(admin.ModelAdmin):
    
    form = ItemForm
    list_display = ['parent', 'label', 'title', 'validated', 'published', 'ref_time']
    
    list_display_links = ['title']
    #actions = ['mark_published', 'mark_not_published']
    
    #inlines = [TranslationInline]
    
    list_editable = ('published', )
    sortable = 'order'
    mptt_level_indent = 20
    
    search_fields = ('slug',
                     'label',
                     'title',
                     'description',
                     'content', )
    
    #date_hierarchy = 'created_date'
    list_filter = [ 'published', ]
    
    readonly_fields = ('related', 'parent', 'origin')
    
    def mark_published(self, request, queryset):
        rows_updated = 0
        for item in queryset.iterator():
            if not item.published:
                item.published = True
                item.save()
                rows_updated += 1
            
        if rows_updated == 1:
            message = _(u"1 item was published.")
        else:
            message = _(u"%s items were published.") % rows_updated
        self.message_user(request, message)

    def mark_not_published(self, request, queryset):
        rows_updated = 0
        for item in queryset.iterator():
            if item.published:
                item.published = False
                item.save()
                rows_updated += 1
            
        if rows_updated == 1:
            message = _(u"1 item was marked as not published.")
        else:
            message = _(u"%s items were marked as not published.") % rows_updated
        self.message_user(request, message)  

admin.site.register(models.Item, ItemAdmin)



def model_link(obj):
    try:
        url = reverse('admin:content_item_change', args=(obj.related.pk,))
        return '<a href="%s">>> Item</a>' % url 
    except:
        return ''

model_link.allow_tags = True


def public_link(obj):
    url = obj.get_url()
    return '<a href="%s" target="_blank" >>> Open</a>' % url

public_link.allow_tags = True

def redirect_link(obj):
    if obj.redirect_url:
        url = obj.redirect_url
        return '<a href="%s" target="_blank" >>> Trans Redirect</a>' % url
    elif obj.related.redirect_url:
        url = obj.related.redirect_url
        return '<a href="%s" target="_blank" >>> Item Redirect</a>' % url
    else:
        url = obj.get_url()
        return '<a href="%s" target="_blank" >>> Page</a>' % url

redirect_link.allow_tags = True



class TranslationAdmin(admin.ModelAdmin):
    form = TranslationForm
    list_display = ['ref_time', 'modified_date', current_url, model_link, 'username', current_slug, current_label, current_title, public_link]
    list_display_links = [current_slug, current_label]
    search_fields = ['slug', 'label', 'title', 'description', 'content']
    ordering = ['-ref_time', '-modified_date']
    
admin.site.register(models.Translation, TranslationAdmin)


class ItemMediaAdminFileWidget(AdminFileWidget):
    def __init__(self, multiuploader_file, *args, **kwargs):
        self.multiuploader_file = multiuploader_file
        super(ItemMediaAdminFileWidget, self).__init__(*args, **kwargs)
    
    def render(self, name, value, attrs=None):
        #setattr(self.multiuploader_file, "url", reverse('multiuploader_file_link', kwargs={'pk': self.multiuploader_file.pk}))
        setattr(self.multiuploader_file, "url", "")
        return super(ItemMediaAdminFileWidget, self).render(name, self.multiuploader_file, attrs)


class ItemMediaAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ItemMediaAdminForm, self).__init__(*args, **kwargs)
        self.fields['file'].widget = ItemMediaAdminFileWidget(multiuploader_file=self.instance)
    class Meta:
        model = Item
        exclude = ('id',)


class ItemMediaAdmin(admin.ModelAdmin):
    form = ItemMediaAdminForm
    search_fields = ["filename", "key_data"]
    list_display = ['related', "filename", "created_date", "file"]
    
#admin.site.register(ItemMedia, ItemMediaAdmin)

