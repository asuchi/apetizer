'''
Created on 15 janv. 2013

@author: rux
'''
import datetime
import logging
import operator
import re

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.db.models.query import QuerySet
from django.http import Http404
from django.http.response import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.context import RequestContext

from apetizer.models import Item, Translation, timestamp_to_datetime, Frontend
from apetizer.views.action import ActionView
from apetizer.views.api import ApiView
from apetizer.views.search import ItemPaginator


log = logging

class ContentView(ApiView, ActionView):
    view_name = 'content'
    view_template = "content/page.html"

    class_actions = ['view', 'cards', 'sitemap', 'medias',  'search', 'map', 'timeline', 'list' ]
    class_actions_forms = {}
    class_action_templates = {
                        'view':'content/page.html',
                        'cards':'content/cards.html',
                        'list':'content/list.html',
                        'medias':'content/medias.html',
                        'sitemap':'content/sitemap.html',
                        'search':'content/search.html',
                        'map':'content/map.html',
                        'timeline':'content/timeline.html',
                        }
    
    @classmethod
    def get_url_regexp(cls, base_path=None, trailing_cap=None):
        """
        Returns a multi-format and multi-action url regexp string for this view
        """
        action_list = cls.get_actions()
        cls_actions = []
        
        for a in action_list:
            cls_actions.append(a.replace('_', '\_'))
        
        #if not base_path or base_path[0] != '^':
        #    url_regexp = '^'
        #else:
        url_regexp = ''
        
        url_regexp += base_path
        
        url_regexp += '(?P<action>('
        url_regexp += '|'.join(cls_actions)
        url_regexp += '))'
        print url_regexp
        return url_regexp
        
        
        if base_path == None:
            url_regexp += '(?P<action>('
            url_regexp += '|'.join(cls_actions)
            url_regexp += '))\/$'
            return url_regexp
        
        else:
            if base_path[-1] == '/':
                url_regexp += base_path[:-1]+''
            else:
                url_regexp += base_path+''
            url_regexp += '(\/|((?P<action>'
            url_regexp += '|'.join(cls_actions)
            url_regexp += ')(\/|\.json)+))$'
            return url_regexp

    def get_context_dict(self, request, user_profile, input_data, **kwargs):
        """
        Return the main template args with page hierarchy
        """
        action = kwargs.get('action')
        
        if request.path_info.endswith('.json'):
            request_path = request.path_info[:-len('.json')]
        else:
            request_path = request.path_info
        
        if request_path.endswith(action+'/'):
            request_path = request_path[:-len(action)-1]
        
        elif request_path.endswith(action):
            request_path = request_path[:-len(action)]
        
        # check for pagination pattern in end of path
        # my-slug-[1,2,3 ... 
        # my-slug-[A,B,C,D ...
        
        template_args = super(ContentView, self).get_context_dict(request, user_profile, input_data, **kwargs)
        
        item_path = Item.objects.get_clean_path(request_path)
        
        # remove action from path
        if item_path and item_path.endswith(action):
            item_path = item_path[:-len(action)-1]
        
        try:
            re_uuid = re.compile("[0-F]{8}-[0-F]{4}-[0-F]{4}-[0-F]{4}-[0-F]{12}", re.I)
            item_parts = Item.objects.get_clean_path(item_path).split('/')
            if len(item_parts) == 2 and re_uuid.findall(item_parts[1]):
                page = Item.objects.get(id=item_parts[1])
            else:
                page = Item.objects.get_at_url(request_path, exact=True)
            
        except ObjectDoesNotExist:
            
            # acces objects by uuid ?
            # remove first slash and check if request path is uid
            # http://stackoverflow.com/questions/136505/searching-for-uuids-in-text-with-regex
        
            try:
                page = Item.objects.get_at_url(item_path, exact=False)
                if not action in ('directory', ):
                    raise Http404
            
            except ObjectDoesNotExist:
                # this means the root item haven't been created yet
                # ensure we have a root page corresponding
                # so we create it as long as the system could not work otherwise
                if len(item_path.split('/')) == 1:
                    root_slug = item_path.split('/')[0]
                    page = Item(slug=root_slug,
                                label=root_slug,
                                title=root_slug,
                                username=user_profile.username,
                                email=user_profile.email,
                                akey=kwargs['pipe']['akey'],
                                action=kwargs['pipe']['action'],
                                path=kwargs['pipe']['path'],
                                locale=kwargs['pipe']['locale'],
                                status='added')
                    page.related_id = page.id
                    page.save()
                else:
                    print root_slug
                    raise Http404
            
        # Check for permission
        if page:
            
            rootNode = page.get_root()
            roots = rootNode.get_children().filter(visible=True).order_by('order')
            
            if page.parent:
                parentNodes = page.parent.get_children().filter(visible=True)
            else:
                parentNodes = rootNode.get_children().filter(visible=True)
            
            nodes = page.get_children()
            nodes = nodes.order_by('order')
            
            #i = 0
            #for n in nodes:
            #    if n.order != i:
            #        n.order = i
            #        n.save()
            #    i+=1
            
            #nodes = nodes[:100]
            
        else:
            raise Http404

        # Check for language
        template_args.update({'currentNode':page,
                              'parentNodes':parentNodes,
                              'rootNode':rootNode,
                              'roots':roots,
                              'nodes':nodes,})
        return template_args
    
    def process(self, request, user_profile, input_data, template_args, **kwargs):
        kwargs['node'] = template_args['currentNode']
        kwargs['pipe']['path'] = template_args['currentNode'].get_url()
        return super(ContentView, self).process(request, user_profile, input_data, template_args, **kwargs)
    
    def process_view(self, request, user_profile, input_data, template_args, **kwargs):
        
        if kwargs['node'].redirect_url and kwargs['node'].visible == False:
            return HttpResponseRedirect(kwargs['node'].redirect_url)
        
        if kwargs['node'].behavior \
            and kwargs['node'].behavior != 'view' \
            and kwargs['node'].behavior in self.actions:
            
            kwargs['action'] = kwargs['node'].behavior
            template_args['action'] = kwargs['action']
            
            return self.process(request, user_profile, {}, template_args, **kwargs)
        else:
            print kwargs['node'].behavior
            return self.render(request, template_args, **kwargs)
    
    def process_cards(self, request, user_profile, input_data, template_args, **kwargs):
        return self.render(request, template_args, **kwargs)
    
    def process_agenda(self, request, user_profile, input_data, template_args, **kwargs):
        queryset = template_args['currentNode'].get_descendants()
        from_date = self.request.GET.get('from', False)
        to_date = self.request.GET.get('to', False)

        if from_date and to_date:
            queryset = queryset.filter(
                start__range=(
                    timestamp_to_datetime(from_date) + datetime.timedelta(-30),
                    timestamp_to_datetime(to_date)
                    )
            )
        elif from_date:
            queryset = queryset.filter(
                start__gte=timestamp_to_datetime(from_date)
            )
        elif to_date:
            queryset = queryset.filter(
                end__lte=timestamp_to_datetime(to_date)
            )

        def event_serializer(events):
            """
            serialize event model
            """
            objects_body = []

            if isinstance(events, QuerySet):
                for event in events:
                    field = {
                        "id": event.pk,
                        "title": event.title,
                        "url": event.related_url,
                        "class": event.css_class,
                        "start": event.start_timestamp,
                        "end": event.end_timestamp
                    }
                    objects_body.append(field)
        
            objects_head = {"success": 1}
            objects_head["result"] = objects_body
            return objects_head
        result_payload = event_serializer(queryset)
        return self.render(request, template_args, result_payload, **kwargs)


    def process_timeline(self, request, user_profile, input_data, template_args, **kwargs):
        template_args['nodes'] = template_args['currentNode'].get_children().exclude(start__isnull=True).order_by('-start')
        return self.render(request, template_args, **kwargs)

    def process_medias(self, request, user_profile, input_data, template_args, **kwargs):
        template_args['nodes'] = template_args['currentNode'].get_children().filter(behavior__in=('upload', 'image'))
        return self.render(request, template_args, **kwargs)

    def process_map(self, request, user_profile, input_data, template_args, **kwargs):
        # draw only descendants points ?
        return self.render(request, template_args, **kwargs)
    
    def process_list(self, request, user_profile, input_data, template_args, **kwargs):
        return self.render(request, template_args, **kwargs)
    
    def process_sitemap(self, request, user_profile, input_data, template_args, **kwargs):
        all_nodes = template_args['currentNode'].get_descendants()
        template_args.update({'all_nodes': all_nodes})
        return self.render(request, template_args, **kwargs)

    def process_search(self, request, user_profile, input_data, template_args, **kwargs):
        """
        http://quepy.machinalis.com/
        """
        keyword = request.GET.get('keyword')
        
        if keyword is None:
            keyword = request.POST.get('keyword', '')
        
        fieldnames = ['title__contains', 'description__contains',
                      'content__contains', 'label__contains', 'slug__contains']
        if keyword:
            qgroup = reduce(operator.or_,
                            (Q(**{fieldname: keyword}) for fieldname in fieldnames))
            translations = Translation.objects.filter(qgroup, related__visible=True).order_by('-modified_date')
            #.exclude(related__published=False).order_by('-modified_date')
        else:
            translations = []
        
        #if translations:
        #    translations.filter(related__published=True)
        nodes = []
        for translation in translations:
            if translation.related and not translation.related in nodes:
                if translation.related.visible:
                    nodes.append(translation.related)
        
        template_args.update({'nodes':nodes, 'keyword':keyword })
        
        return self.render(request, template_args, **kwargs)
    
    def render_html(self, request, template_args, result_message, result_status,
                    **kwargs):
        if template_args['nodes'] and len(template_args['nodes']):
            template_args['paginator'] = ItemPaginator(template_args['nodes'], 25)
            if request.GET.get('page'):
                template_args['current_page'] = template_args['paginator'].page(kwargs['pipe']['data'].get('page',1))
            else:
                template_args['current_page'] = template_args['paginator'].page(1)
        
        if kwargs['action'] in ContentView.class_actions:
            return super(ContentView, self).render_html(request, template_args,
                                                   result_message, result_status,
                                                   **kwargs)
        
        
        action = kwargs.get('action', ContentView.default_action)

        if type(result_status) != type(200):
            if result_status in ('warning', 'success', 'ok'):
                result_status = 200
            else:
                result_status = 500
        
        templates = [self.action_templates.get(action, self.view_template)]
        
        if action == 'index':
            page_template = template_args['currentNode'].get_root().slug+'/index.html'
            templates.insert(0, page_template)
            
            if template_args['currentNode'].parent:
                page_template = template_args['currentNode'].get_path()+'.html'
                templates.insert(0, page_template)
                
            # is there a corresponding django site ?
            if request.__dict__.get('site'):
                current_frontend = Frontend.objects.get(site_ptr_id=request.site.id)
                
                page_template = current_frontend.folder_name+'/index.html'
                templates.insert(0, page_template)

                page_template = current_frontend.folder_name+'/pages/'+template_args['currentNode'].slug+'.html'
                templates.insert(0, page_template)
            
            #elif template_args['currentNode'].visible:

            
        
        return render_to_response(templates,
                                  template_args,
                                  context_instance=RequestContext(request),)





