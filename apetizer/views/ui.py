'''
Created on 15 janv. 2013

@author: rux
'''

import logging
import os.path

from django.contrib import messages
from django.core.files.uploadedfile import UploadedFile
from django.core.signing import Signer, BadSignature
from django.forms.models import model_to_dict
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import redirect, render_to_response
from django.template.context import RequestContext
from django.utils.text import slugify
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _, get_language
from apetizer.forms.content import ItemTranslateForm, ItemDeleteForm, \
    MultiUploadForm, ItemAddForm, ItemPutForm, ItemLocationForm, \
    ItemTimingForm, ItemDataForm, ItemRelatedForm, ItemImageForm, \
    ItemCodeForm, ItemRedirectForm, ItemPublishForm, ItemRenameForm, \
    ItemReorderForm, ItemFileForm
from apetizer.models import Item, Translation, Moderation, get_new_uuid
from apetizer.parsers.api_json import load_json, dump_json
from apetizer.utils.compatibility import unicode3
from apetizer.views.moderate import ModerateView
from apetizer.views.notebook import NotebookView
from apetizer.views.program import ProgramView
from apetizer.views.visitor import VisitorView
from apetizer.views.items import ItemView


log = logging

message_deactivated_action = _('Sorry, this action requires a fully registred login.')

class UIView(NotebookView, ItemView, ProgramView, ModerateView, VisitorView):
    
    view_name = 'ui'
    view_template = "ui/base.html"

    class_actions = ['add', 'change', 'file', 
                     'translate', 'delete', 'data', 
                     'image', 'content', 'search', 
                     'location', 'timing', 
                     'redirect', 'publish', 'reorder', 
                     'rename', 'related', 'upload'
                     ]

    class_actions_forms = {
                    'add':(ItemAddForm,),
                    'put':(ItemPutForm,),
                    'reorder':(ItemReorderForm,),
                    'translate':(ItemTranslateForm,),
                    'location':(ItemLocationForm,),
                    'timing':(ItemTimingForm,),
                    'delete':(ItemDeleteForm,),
                    
                    'redirect':(ItemRedirectForm,),
                    
                    'image':(ItemImageForm,),
                    'file':(ItemFileForm,),
                    
                    'rename':(ItemRenameForm,),

                    'data':(ItemDataForm,),
                    'content':(ItemCodeForm,),
                    
                    'publish':(ItemPublishForm,),
                    'related':(ItemRelatedForm,),
                    }
    
    class_action_templates = {
                        'add':'ui/add.html',
                        
                        'change':'content/page.html',
                        'translate':'ui/translate.html',
                        'redirect':'ui/change.html',
                        'image':'ui/image.html',
                        'file':'ui/file.html',
                        'delete':'ui/change.html',
                        
                        'rename':'ui/change.html',

                        'data':'ui/data.html',
                        'upload':'ui/upload.html',
                        'location':'ui/location.html',
                        'timing':'ui/timing.html',
                        'publish':'ui/publish.html',
                        
                        'redirect':'ui/redirect.html',
                        
                        'content':'ui/content.html',
                              
                        'reorder':'ui/change.html',
                        
                        'related':'ui/related.html',
                        }
    
    def get_forms_instances(self, action, user_profile, kwargs):
        
        if action in UIView.class_actions:
            
            if action in ('translate', 'redirect', 'content', 'rename'):
                
                # load a new translation cloning the existing one
                trans_data = model_to_dict(kwargs['node'])
                
                user_data = model_to_dict(user_profile)
                
                trans_data.update(user_data)
                for key in list(trans_data.keys()):
                    if not key in Item.__localizable__:
                        del trans_data[key]
                
                trans_data['locale'] = get_language()
                trans_data['path'] = kwargs['node'].path
                
                trans_data['akey'] = user_profile.akey
                trans_data['username'] = user_profile.username
                trans_data['email'] = user_profile.email
                trans_data['validated'] = user_profile.validated
                
                trans_data['related_id'] = kwargs['node'].id
                
                trans_data['action'] = kwargs['action']
                
                trans_data['status'] = 'changed'
                trans_data['subject'] = 'Changed texts'
                trans_data['message'] = 'Text have been changed'
                trans_data['visible'] = True
                
                translation = Translation(**trans_data)
                
                return (translation,)
            
            elif 'instances' in kwargs:
                return kwargs['instances']
            
            elif action in ('add', 'put'):
                
                parentNode = kwargs['node']
                
                item = Item()
                item.parent = parentNode
                item.locale = get_language()
                item.get_translation()
                
                item.akey=user_profile.akey
                item.username=user_profile.username
                item.email=user_profile.email
                item.validated=user_profile.validated
                
                item.action='add'
                item.status='added'
                item.subject='Ajout'
                item.message='Nouvel element ajoute'
                
                item.path = parentNode.get_path()
                
                item.related_id = item.id
                
                return (item,)
            else:
                return (kwargs['node'],)
        else:
            return super(UIView, self).get_forms_instances(action, user_profile, kwargs)
    
    
    def process(self, request, user_profile, input_data, template_args, **kwargs):
        
        if kwargs.get('action') in self.class_actions:
            if not user_profile.validated \
                or not request.user.is_authenticated():
                messages.error(request, message_deactivated_action)
                return HttpResponseRedirect('login/?next='+request.path)
        
        return super(UIView, self).process(request, user_profile, input_data, template_args, **kwargs)

    def process_add(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Add a new item
        """
        return self.manage_item_pipe(request, user_profile, input_data, template_args, **kwargs)
    
    def process_put(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Put properties to an existing or new item
        """
        if input_data.has_key('id'):
            try:
                kwargs['instances'] = (Item.objects.get(input_data['id']))
            except:
                return self.render(request, template_args, {}, 'Object not found', 404)
        
        return self.manage_item_pipe(request, user_profile, input_data, template_args, **kwargs)
    
    def process_rename(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Renaming an item properties
        """
        return self.manage_translation_pipe(request, user_profile, input_data, template_args, **kwargs)

    def process_translate(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Edit an item translation
        """
        return self.manage_translation_pipe(request, user_profile, input_data, template_args, **kwargs)
    
    
    def process_content(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Edit an item translation content
        """
        return self.manage_translation_pipe(request, user_profile, input_data, template_args, **kwargs)

    
    def process_redirect(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Edit an item translation
        """
        return self.manage_translation_pipe(request, user_profile, input_data, template_args, **kwargs)
    

    
    def process_timing(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Edit an item location
        """
        return self.manage_item_pipe(request, user_profile, input_data, template_args, **kwargs)

    
    
    def process_change(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Edit an item properties
        """
        return self.manage_item_pipe(request, user_profile, input_data, template_args, **kwargs)
    
    
    def process_history(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Show item history and manages it's consolidation options
        """
        raise NotImplementedError

    
    def process_reorder(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Change the item order
        """
        return self.manage_item_pipe(request, user_profile, input_data, template_args, **kwargs)
    
    def process_image(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Upload an image to the selected item
        """
        return self.manage_item_pipe(request, user_profile, input_data, template_args, **kwargs)

    def process_file(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Upload an image to the selected item
        """
        return self.manage_item_pipe(request, user_profile, input_data, template_args, **kwargs)


    def process_publish(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Switch current object publishing state
        """
        return self.manage_item_pipe(request, user_profile, input_data, template_args, **kwargs)


    def process_data(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Show current item data
        """
        return self.manage_item_pipe(request, user_profile, input_data, template_args, **kwargs)

    def process_location(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Edit an item location
        Soon to be implemented with geohash
        You can import geojson data directly
        """
        # load fields from geojson if not in input_data
        # convert input_data fields to geohash and geodata
        # update input_data
        #raise NotImplementedError
        
        return self.manage_item_pipe(request, user_profile, input_data, template_args, **kwargs)




    def process_sync(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Sync an item with another item
        """
        raise NotImplementedError
    
    
    def process_revert(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Revert an item to a previous version
        """
        raise NotImplementedError




    def process_delete(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Delete an item
        """
        item_form, = self.get_validated_forms((template_args['currentNode'],), input_data, 'delete', save_forms=False, files=request.FILES)
        if item_form.is_valid():
            if template_args['currentNode'].parent == None or template_args['currentNode'].parent.parent == None:
                response = HttpResponseRedirect('/')
            else:
                response = HttpResponseRedirect(template_args['currentNode'].parent.get_url())
            
            template_args['currentNode'].visible = False
            if template_args['currentNode'].parent:
                template_args['currentNode'].redirect_url = template_args['currentNode'].parent.get_url()
            template_args['currentNode'].save()
            
            return response
        
        template_args['action_forms'] = (item_form,)
        return self.manage_item_pipe(request, user_profile, input_data, template_args, **kwargs)
        return self.render(request, template_args, **kwargs)


    def process_upload(self, request, user_profile, input_data, template_args, noajax=False, **kwargs):
        """
        Main Multiuploader module.
        Parses data from jQuery plugin and makes database changes.
        """
        
        if request.method == 'POST':
            log.info('received POST to main multiuploader view')
    
            if request.FILES is None:
                response_data = [{"error": _('Must have files attached!')}]
                return HttpResponse(dump_json(response_data))
    
            if not u'form_type' in request.POST:
                response_data = [{"error": _("Error when detecting form type, form_type is missing")}]
                return HttpResponse(dump_json(response_data))
    
            signer = Signer()
    
            try:
                form_type = signer.unsign(request.POST.get(u"form_type"))
            except BadSignature:
                response_data = [{"error": _("Tampering detected!")}]
                return HttpResponse(dump_json(response_data))
    
            form = MultiUploadForm(request.POST, request.FILES, form_type=form_type)
            
            if not form.is_valid():
                error = _("Unknown error")
    
                if "file" in form._errors and len(form._errors["file"]) > 0:
                    error = form._errors["file"][0]
    
                response_data = [{"error": error}]
                return HttpResponse(dump_json(response_data))
            
            rfile = request.FILES[u'file']
            wrapped_file = UploadedFile(rfile)
            filename = wrapped_file.name
            file_size = wrapped_file.file.size
            
            fname, ext = os.path.splitext(filename)
            
            as_image = False
            if ext.lower() in ('.jpg', '.jpeg', '.png', '.gif'):
                as_image = True
            
            
            log.info('Got file: "%s"' % filename)
            
            itemModel = template_args.get('currentNode')
            
            fl = Item(id=get_new_uuid())
            
            fl.action = 'upload'
            fl.path = itemModel.get_url()
            
            fl.akey = user_profile.akey
            
            fl.email = user_profile.email
            fl.username = user_profile.username
            
            fl.validated = user_profile.validated
            
            fl.slug = slugify(filename)
            fl.title = filename
            fl.parent = itemModel
            
            fl.file = rfile
            
            if as_image == True:
                fl.behavior = 'image'
                fl.label = input_data.get('label', 'Image')
                fl.order = input_data.get('order', 0)
                fl.image = rfile
            else:
                # TODO
                fl.behavior = 'upload'
                fl.label = input_data.get('label', 'Fichier')
                fl.order = input_data.get('order', 0)
                # set screenshot of document or icon
                #fl.image = rfile
            
            fl.status = 'uploaded'
            fl.locale = get_language()
            
            fl.subject = 'Fichier ajoute'
            fl.message = 'Le fichier '+filename+' a ete ajoute'
            
            fl.save()
            
            thumb_url = "" #get_thumbnail(fl.file, "80x80", quality=50)
            file_link_url = "" #reverse('multiuploader_file_link', args=[fl.pk]),
            delete_url = "" #reverse('multiuploader_delete', args=[fl.pk])
            
            #generating json response array
            result = [{"id": str(fl.id),
                       "name": filename,
                       "size": file_size,
                       "url": file_link_url,
                       "thumbnail_url": thumb_url,
                       "delete_url": delete_url,
                       "delete_type": "POST", }]
            
            response_data = dump_json(result)
            
            #checking for json data type
            #big thanks to Guy Shapiro
            
            if noajax:
                if request.META['HTTP_REFERER']:
                    redirect(request.META['HTTP_REFERER'])
            
            if "application/json" in request.META['HTTP_ACCEPT_ENCODING']:
                mimetype = 'application/json'
            else:
                mimetype = 'text/plain'
            return HttpResponse(response_data, content_type=mimetype)
        else:  # GET
            template_args['multiuploader_form'] = MultiUploadForm(form_type='default')
        
        return self.manage_item_pipe(request, user_profile, input_data, template_args, **kwargs)
        return self.render(request, template_args, **kwargs)
    
    
    
    def process_related(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Displays and manages the item related_url
        """
        return self.manage_item_pipe(request, user_profile, input_data, template_args, **kwargs)


    
    
    def manage_translation_pipe(self, request, user_profile, input_data, template_args, **kwargs):
        
        translation = kwargs['node'].get_translation()
        
        slug = translation.slug
        
        reloaded = False
        
        # is there a proposal from user_profile ?
        if self.is_proposal(user_profile, translation, **kwargs):
            try:
                if user_profile.email:
                    proposal = Moderation.objects.filter(related=translation.related, email=user_profile.email, action=kwargs['action'], status='proposed').order_by('-ref_time')[0]
                else:
                    proposal = Moderation.objects.filter(related=translation.related, akey=user_profile.akey, action=kwargs['action'], status='proposed').order_by('-ref_time')[0]
                
                messages.warning(request, 'Your proposal have already been posted but you can still modify it !')
                
                new_data = load_json(proposal.data)
                new_data.update(input_data)
                input_data = new_data
                if request.method.lower() == 'get':
                    reloaded = True
            except IndexError:
                pass
        
        if reloaded:
            template_args['action_forms'] = self.get_validated_forms(self.get_forms_instances(kwargs['action'], user_profile, kwargs), input_data, kwargs['action'], save_forms=False, files=request.FILES)
            self.validate_action_forms(request, template_args['action_forms'])
            return self.render(request, template_args, **kwargs)
        else:
            return self.manage_pipe(request, user_profile, input_data, template_args, **kwargs)
    
    def is_proposal(self, user_profile, item, **kwargs):
        """
        Defines if the user_profile will set it's changes as a proposal
        A proposal is raised when the user_profile is not validated
        
        Override this method to get better rights management
        """
        if kwargs['action'] in UIView.class_actions:
            if user_profile.validated == None and item.validated:
                return True
            else:
                return super(UIView, self).is_proposal(user_profile, item, **kwargs)
        else:
            return super(UIView, self).is_proposal(user_profile, item, **kwargs)


    def manage_item_pipe(self, request, user_profile, input_data, template_args, **kwargs):
        
        item = template_args['currentNode']
        action = kwargs.get('action')
        
        reloaded = False
        
        # is there a proposal from user_profile ?
        if self.is_proposal(user_profile, item, **kwargs):
            try:
                if user_profile.email:
                    proposal = Moderation.objects.filter(related=item, email=user_profile.email, action=kwargs['action'], status='proposed').order_by('-ref_time')[0]
                else:
                    proposal = Moderation.objects.filter(related=item, akey=user_profile.akey, action=kwargs['action'], status='proposed').order_by('-ref_time')[0]
                
                messages.warning(request, 'Your proposal have already been posted but you can modify it !')
                
                new_data = load_json(proposal.data)
                new_data.update(input_data)
                input_data = new_data
                
                if request.method.lower() == 'get':
                    reloaded = True
                    
            except IndexError:
                pass
        
        if reloaded:
            template_args['action_forms'] = self.get_validated_forms(self.get_forms_instances(kwargs['action'], user_profile, kwargs), input_data, kwargs['action'], save_forms=False, files=request.FILES)
            self.validate_action_forms(request, template_args['action_forms'])
            return self.render(request, template_args, {}, **kwargs)
        else:
            return self.manage_pipe(request, user_profile, input_data, template_args, **kwargs)


    def manage_action_completed(self, request, user_profile, template_args, **kwargs):
        """
        Handles final pipe action view state
        """
        action = kwargs['action']
        if action in self.class_actions:
            return HttpResponseRedirect(template_args['currentNode'].get_url()+'view/')
        else:
            return super(UIView, self).manage_action_completed(request, user_profile, template_args, **kwargs)



    def create_proposal(self, request, user_profile, input_data, template_args, **kwargs):
        
        # create a moderation with the request 
        # action and data and a proposal status
        mod = Moderation()
        
        mod.akey = user_profile.akey
        mod.email = user_profile.email
        mod.username = user_profile.username
        mod.locale = get_language()
        
        mod.subject = 'Wants to change'
        mod.message = 'Wants to change'
        
        mod.action = kwargs['action']
        mod.data = dump_json(input_data)
        
        mod.status = 'proposed'
        
        mod.path = kwargs['node'].path
        
        mod.related_id = kwargs['node'].id
        
        mod.visible = False
        mod.completed_date = now()
        mod.save()
        
        messages.warning(request, 'Your proposal have been posted !')
        
        return HttpResponseRedirect(kwargs['node'].get_url()+'view/')


    def render_html(self, request, template_args, result_message, result_status,
                    **kwargs):
        
        if not kwargs['action'] in self.__class__.class_actions:
            return super(UIView, self).render_html(request, template_args,
                                                   result_message, result_status,
                                                   **kwargs)
        
        action = kwargs.get('action', UIView.default_action)

        if type(result_status) != type(200):
            if result_status in ('warning', 'success', 'ok'):
                result_status = 200
            else:
                result_status = 500

        templates = [self.action_templates.get(action, self.view_template)]
        
        return render_to_response(templates,
                                  template_args,
                                  context_instance=RequestContext(request),)


