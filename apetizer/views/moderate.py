'''
Created on 6 juil. 2015

@author: rux
'''
from collections import OrderedDict
import json

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.http.response import HttpResponseRedirect
from django.utils.translation import get_language

from apetizer.forms.moderate import ModerateInviteForm, ModerateCommentForm, \
    ModerateContactForm, ModerateReviewForm, ModerateFollowForm, \
    ModerateUnfollowForm, ModerateDiscussForm, ModerateConsultForm
from apetizer.models import Moderation, get_new_uuid
from apetizer.views.content import ContentView
from apetizer.views.pipe import ActionPipeView
from apetizer.parsers.json import load_json


class ModerateView(ContentView, ActionPipeView):
    view_name = 'moderate'
    view_template = 'moderate/base.html'
    class_actions = ['discuss', 'invite', 'comment', 'contact', 'review',
                     'accept', 'reject', 'follow', 'unfollow', 'consult']
    
    class_actions_forms = {'invite':(ModerateInviteForm,),
                           'contact': (ModerateContactForm,),
                           'comment':(ModerateCommentForm,),
                           'review':(ModerateReviewForm,),

                           'discuss':(ModerateDiscussForm,),
                           
                           'follow':(ModerateFollowForm,),
                           'unfollow':(ModerateUnfollowForm,),
                           
                           'consult':(ModerateConsultForm,),
                           }
    
    class_action_templates = {
                    'invite':'moderate/invite.html',
                    'comment': 'moderate/comment.html',
                    'discuss': 'moderate/discuss.html',
                    'contact': 'moderate/contact.html',
                    'review': 'moderate/review.html',
                    
                    'consult': 'moderate/consult.html',
                    
                    'accept':'moderate/accept.html',
                    'reject': 'moderate/reject.html',
                    
                    'follow':'ui/change.html',
                    'unfollow': 'ui/change.html',
                    }
    
    comment_auto_invite = False
    comment_require_validation = False
    
    def __init__(self, *args, **kwargs):
        super(ModerateView, self).__init__(*args, **kwargs)
        
        contact_scenario =OrderedDict([
                                      ('email',
                                           {'class': self.__class__,
                                            'action': 'profile'}),
                                      ('username',
                                           {'class': self.__class__,
                                            'action': 'profile'}),
                                      ])
        
        self.action_scenarios['contact'] = contact_scenario
        self.action_scenarios['invite'] = contact_scenario

        
    def get_forms_instances(self, action, user_profile, kwargs):
        
        if action in ModerateView.class_actions:
            pipe_data = kwargs.get('pipe')['data']
            akey = kwargs.get('pipe')['akey']
            return (self.get_moderation(akey, user_profile, pipe_data, **kwargs),)
        else:
            return super(ModerateView, self).get_forms_instances(action, user_profile, kwargs)
    
    def get_moderation(self, akey, user_profile, data, node, **kwargs):
        
        new_moderation = Moderation()
        
        new_moderation.akey = akey
        new_moderation.action = kwargs['action']
        new_moderation.locale = get_language()
        new_moderation.path = node.get_url()
        
        new_moderation.related = node
        
        new_moderation.username = user_profile.username
        new_moderation.email = user_profile.email
        new_moderation.validated = user_profile.validated
        
        if kwargs['action'] == 'comment':
            new_moderation.subject = 'Nouveau commentaire'
        
        elif kwargs['action'] == 'review':
            new_moderation.subject = 'Nouvel avis'
        
        elif kwargs['action'] == 'discuss':
            new_moderation.subject = 'Nouveau message'
        
        
        
        return new_moderation
    
    
    def process_accept(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Accept a proposal
        """
        # switch action and data from the proposal
        proposal_uid = input_data['token']
        proposal = Moderation.objects.get(id=proposal_uid)
        
        # re-run the action
        kwargs['action'] = proposal.action
        template_args['action'] = proposal.action
        
        # simulate a post ??
        request.method = 'POST'
        
        proposal_transfer = input_data.get('transfer','no')
        
        if proposal_transfer != 'no':
            input_data = load_json(proposal.data)
            input_data.email = proposal.email
            input_data.username = proposal.username
            response = self.process(request, user_profile, input_data, template_args, **kwargs)
        else:
            response = self.process(request, user_profile, load_json(proposal.data), template_args, **kwargs)
        
        proposal.status = 'accepted'
        proposal.save()
        
        # check for older action proposals
        #older_proposals = Moderation.objects.filter(related=proposal.related, status='proposed', action=kwargs['action'])
        #older_proposals.update(status='rejected')
        #older_proposals.save()
        
        return response



    def process_reject(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Reject a proposal
        """
        proposal_uid = input_data['token']
        proposal = Moderation.objects.get(id=proposal_uid)
        
        proposal.status = 'rejected'
        proposal.save()
        
        return HttpResponseRedirect(kwargs['node'].get_url())


    def process_follow(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Follow the object changes
        """
        # check for an existing following state
        try:
            Moderation.objects.get(related_id=kwargs['node'].id, status='following')
            messages.warning(request, 'You are already following this item')
        except ObjectDoesNotExist:
            if input_data.get('follow'):
                moderation, = self.get_forms_instances('follow', user_profile, kwargs)
                moderation.status = 'following'
                moderation.save()
                messages.success(request, 'You are now following this item')
            else:
                # maybe form is wrong ?
                return self.manage_pipe(request, user_profile, input_data, template_args, **kwargs)
        
        return HttpResponseRedirect(kwargs['node'].get_url()+'view/')
    
    def process_unfollow(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Unfollow the object changes
        """
        try:
            moderation = Moderation.objects.get(related_id=kwargs['node'].id, status='following')
            if input_data.get('unfollow'):
                moderation.status = 'followed'
                moderation.save()
                messages.success(request, 'You not following this item anymore')
                return HttpResponseRedirect(kwargs['node'].get_url()+'view/')
            else:
                return self.manage_pipe(request, user_profile, input_data, template_args, **kwargs)

        except ObjectDoesNotExist:
            messages.warning(request, 'You are not actually following this item')
            return HttpResponseRedirect(kwargs['node'].get_url()+'view/')

    def process_contact(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Contact the creator
        """
        return self.manage_pipe(request, user_profile, input_data, template_args, **kwargs)

    def process_comment(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Comment the related item
        """
        return self.manage_pipe(request, user_profile, input_data, template_args, **kwargs)
    
    def process_discuss(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Discuss about the related item
        """
        return self.manage_pipe(request, user_profile, input_data, template_args, **kwargs)


    def process_consult(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Consult me and the item changes
        """
        # gether the whole item moderations statuses
        statuses = ['commented','changed','told']
        
        # filter by the selected status
        if input_data.get('status'):
            template_args['history'] = kwargs['node'].get_history().filter(status__in=(input_data.get('status'),))
        else:
            template_args['history'] = kwargs['node'].get_history()
        
        # check for related item nodes
        template_args['action_forms'] = self.get_validated_forms( tuple(), input_data, kwargs['action'], save_forms = False, bound_forms=False)
        return self.render(request, template_args, **kwargs)
    
    def process_review(self, request, user_profile, input_data, template_args, **kwargs):
        """
        Review an item
        """
        return self.manage_pipe(request, user_profile, input_data, template_args, **kwargs)

    
    def process_invite(self, request, user_profile, input_data, template_args, **kwargs):
        """
        invite a group of user to join the commenting
        """
        akey = self.get_session_user_keys(request)
        action_data = kwargs['pipe']
        action = kwargs.get('action')
        emails = input_data.get('emails')
       

        # establish a list of invitation
        invitationList = {}
        # from email list
        if emails:
            for email in emails.split(','):
                invitationList[email] = None
        
        origin, = self.get_forms_instances(action, user_profile, kwargs)
        
        #
        for iemail in invitationList:
            invitation = Moderation()
            invitation.origin = origin
            invitation.related_id = template_args['currentNode'].id
            invitation.action = 'invite'
            invitation.locale = get_language()
            invitation.path = kwargs['node'].get_url()
            invitation.status = 'invited'
            invitation.email = iemail
            invitation.akey = get_new_uuid()
            invitation.subject = 'Invitation lancee !'
            invitation.message = input_data.get('message', 'Vous etes invite a consulter ce document')
            invitation.save()
        
        template_args['action_forms'] = self.get_validated_forms(
                                                 self.get_forms_instances(action, user_profile, kwargs),
                                                 input_data,
                                                 action,
                                                 save_forms=False,
                                                 bound_forms=False
                                                 )

        return self.render(request, template_args, **kwargs)

    def process_Zcomment(self, request, user_profile, input_data, template_args,
                        **kwargs):
        """
        post a user comment with or without vote
        """
        # filter posted data and update
        akey = self.get_session_user_keys(request)
        action_data = kwargs['pipe']
        action = kwargs.get('action')

        # fill forms
        comment_form, = self.get_validated_forms(self.get_forms_instances(action, user_profile, kwargs),
                                                 input_data,
                                                 action,
                                                 save_forms=False,
                                                 files=request.FILES
                                                 )
        template_args['comment_form'] = comment_form
        
        moderation_list = Moderation.objects.filter(related=template_args['currentNode'])

        #to refacto : some mecanisme with visitor.
        if 'email' in input_data and input_data['email']:
            email = input_data.get('email')
        else:
            email = user_profile.email

        userReview = None
        for review in moderation_list:
            if review.email == email and review.status != 'comment':
                userReview = review
        if not userReview:
            userReview = Moderation(akey=user_profile.akey,
                                    username=user_profile.username,
                                    email=user_profile.email,
                                    validated=user_profile.validated,
                                    related=template_args['currentNode'],
                                    subject='Welcome',
                                    message='Welcome to the thread',
                                    )

        userReview = self.update_moderation(request, user_profile, input_data, 
                                            model=template_args['currentNode'])

        moderation_list = Moderation.objects.filter(related=template_args['currentNode'],status__in=('comment',))
        
        review = self.display_view(request, moderation_list, userReview)

        template_args.update({
                'review': review,
                'evaluated': self.is_evaluated(email, template_args['currentNode'])
                })

        return self.render(request, template_args, **kwargs)


    def display_view(self, request, reviews, userReview):

        comments = []
        reviewers = []
        userReviews = {}

        for r in reviews:
            if r.status in ('accepted','rejected'):
                userReviews[r.email] = r
            #if r.status == 'comment' or r.status == 'accepted' or r.status == 'rejected':
            comments.append(r)

        for i, r in userReviews.iteritems():
            reviewers.append(r)

        lastUserReviews = []
        for i, r in userReviews.iteritems():
            reviewItem = {}
            if r.modified_date:
                reviewItem['date'] = r.modified_date
            else:
                reviewItem['date'] = r.created_date
            reviewItem['status'] = r.status
            reviewItem['subject'] = r.subject
            reviewItem['message'] = r.message
            lastUserReviews.append(reviewItem)

        review = {}
        review['user_review'] = userReview
        review['user_reviews'] = lastUserReviews
        review['reviewers'] = reviewers
        review['comments'] = comments
        return review

    def update_moderation(self, request, user_profile, input_data, model):
        """
        Les donnees du pipe doivent contenir l'ensemble des donnees, validees
        """
        newStatus = input_data.get('new_status',False)

        try:
            evaluation = int(input_data.get('new_evaluation', 0))
        except Exception:
            evaluation = 0

        if newStatus:
            newReview = Moderation()
            
            newReview.akey=user_profile.akey
            newReview.username=user_profile.username
            newReview.email=user_profile.email
            newReview.validated=user_profile.validated
            
            newReview.related_id = model.id
            
            newReview.status = newStatus
            newReview.evaluation = evaluation

            newReview.message = newStatus
            newReview.subject = newStatus
            newReview.message = ' A vote !'
            newReview.save()
            #TODO check if it is usefull or not
            if newStatus == newReview.status:
                self.broadcast_message(newReview)
        
        # check for new comment
        newComment = input_data.get('new_comment', False)
        
        if (type(newComment) == str or type(newComment) == unicode ) and newComment.strip() == '':
            newComment = 'Pas de commentaire'

        if newComment:
            commentReview = Moderation()
            commentReview.related=model
            commentReview.akey=user_profile.akey
            commentReview.username=user_profile.username
            commentReview.email=user_profile.email
            commentReview.validated=user_profile.validated
            
            commentReview.status = 'comment'
            commentReview.subject = 'Commentaire'
            commentReview.message = newComment
            commentReview.is_sent = False
            commentReview.evaluation = evaluation
            
            commentReview.action = 'comment'
            commentReview.locale = get_language()
            commentReview.path = model.get_url()
            
            commentReview.save()
            self.broadcast_message(commentReview)

        #if userReview.status == 'unread':
        #    userReview.status = 'reviewing'
        #    userReview.save()
            # TODO
            # create a new moderation entry logging the action

        #return userReview

    def send_message(self, review):
        """
        Override this view to set your own message system
        """
        # send an email to review.email
        emailtitle = review.subject
        emailcontent = str(review.message)
        if review.content:
            emailcontent += "\n----------------------------------------------------\n\n"
            emailcontent += str(review.content)
            emailcontent += "\n\n-------------------------------------------------------\n"
            emailcontent += "document:\n"
            emailcontent += "------------------------------------------------\n"

    def broadcast_message(self, message):
        """
        Override this method to set your own broadcasting method
        """
        return False

    def is_evaluated(self, email, model):
        return Moderation.objects.filter(related=model, 
                                         email=email, status="comment").count() > 0

    def is_first_comment(self, email, model):
        return Moderation.objects.filter(email=email, related=model).count() == 0
