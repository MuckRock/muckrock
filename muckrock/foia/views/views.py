"""
Views for the FOIA application
"""

from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string, get_template
from django.template import RequestContext
from django.utils import simplejson
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from datetime import datetime
import logging
import stripe
from random import random, randint, choice
import string

from muckrock.accounts.forms import PaymentForm
from muckrock.accounts.models import Profile
from muckrock.agency.models import Agency
from muckrock.foia.codes import CODES
from muckrock.foia.forms import \
    ListFilterForm, \
    MyListFilterForm
from muckrock.foia.models import \
    FOIARequest, \
    FOIAMultiRequest, \
    FOIACommunication, \
    STATUS
from muckrock.foia.views.comms import move_comm, delete_comm, save_foia_comm, resend_comm
from muckrock.foia.views.composers import get_foia
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.qanda.models import Question
from muckrock.settings import STRIPE_PUB_KEY, STRIPE_SECRET_KEY, MONTHLY_REQUESTS
from muckrock.sidebar.models import Sidebar
from muckrock.tags.models import Tag
from muckrock.views import class_view_decorator

# pylint: disable=R0901

logger = logging.getLogger(__name__)
stripe.api_key = STRIPE_SECRET_KEY
STATUS_NODRAFT = [st for st in STATUS if st != ('started', 'Draft')]

class List(ListView):
    """Base list view for other list views to inherit from"""

    def filter_sort_requests(self, foia_requests, update_top=False):
        """Sorts the FOIA requests"""
        get = self.request.GET
        order = get.get('order', 'desc')
        sort = get.get('sort', 'date_submitted')
        filter = {
            'status': get.get('status', False),
            'agency': get.get('agency', False),
            'jurisdiction': get.get('jurisdiction', False),
            'user': get.get('user', False),
            'tags': get.get('tags', False)
        }
        
        # TODO: handle a list of tags
        for key, value in filter.iteritems():
            if value:
                print value
                if key == 'status':
                    foia_requests = foia_requests.filter(status=value)
                elif key == 'agency': 
                    a = get_object_or_404(Agency, id=value)
                    foia_requests = foia_requests.filter(agency=a)
                elif key == 'jurisdiction':
                    value = value.split(',')
                    j = get_object_or_404(Jurisdiction, id=value[0])
                    foia_requests = foia_requests.filter(jurisdiction=j)
                elif key == 'user':
                    u = get_object_or_404(User, name=value)
                    foia_requests = foia_requests.filter(user=u)
                elif key == 'tags':
                    foia_requests = foia_requests.filter(tags__contains=value)
                    

        # Handle extra cases by resorting to default values
        if order not in ['asc', 'desc']:
            order = 'desc'
        if sort not in ['title', 'date_submitted', 'times_viewed']:
            sort = 'date_submitted'
        ob_field = '-' + sort if order == 'desc' else sort
        if update_top: # only for MyList
            foia_requests = foia_requests.order_by('-updated', ob_field)
        else:
            foia_requests = foia_requests.order_by(ob_field)
        
        return foia_requests

    def get_paginate_by(self, queryset):
        try:
            return min(int(self.request.GET.get('per_page', 10)), 100)
        except ValueError:
            return 10

    def get_context_data(self, **kwargs):
        context = super(List, self).get_context_data(**kwargs)
        # get args to populate initial values for ListFilterForm
        get = self.request.GET
        form_fields = {
            'order': get.get('order', False),
            'sort': get.get('sort', False),
            'status': get.get('status', False),
            'agency': get.get('agency', False),
            'jurisdiction': get.get('jurisdiction', False),
            'user': get.get('user', False),
            'tags': get.get('tags', False)
        }
        form_initials = {}
        filter_url = ''
        for key, value in form_fields.iteritems():
            if value:
                form_initials.update({key: value})
                filter_query = '&' + str(key) + '=' + str(value)
                filter_url += filter_query
        
        context['title'] = 'FOI Requests'
        context['form'] = ListFilterForm(initial=form_initials)
        context['filter_url'] = filter_url
        return context
    
    def get_queryset(self):
        query = FOIARequest.objects.get_viewable(self.request.user)
        return self.filter_sort_requests(query)
    
    '''
    def get(self):
        cleaned_url = self.request.GET.copy().urlencode()
        return redirect(cleaned_url)
    '''

@class_view_decorator(login_required)
class MyList(List):
    """View requests owned by current user"""
    template_name = 'lists/request_my_list.html'

    def set_read_status(self, foia_pks, status):
        """Mark requests as read or unread"""
        for foia_pk in foia_pks:
            foia = FOIARequest.objects.get(pk=foia_pk, user=self.request.user)
            foia.updated = status
            foia.save()

    def post(self, request):
        """Handle updating tags"""
        try:
            post = request.POST
            foia_pks = post.getlist('foia')
            if post.get('submit') == 'Mark as Read':
                self.set_read_status(foia_pks, False)
            elif post.get('submit') == 'Mark as Unread':
                self.set_read_status(foia_pks, True)
            elif post.get('submit') == 'Mark All as Read':
                all_unread = [foia.pk for foia in  FOIARequest.objects.filter(user=self.request.user, updated=True)]
                self.set_read_status(all_unread, False)
        except (FOIARequest.DoesNotExist):
            pass
        return redirect('foia-mylist')

    def merge_requests(self, foia_requests, multi_requests):
        """Merges the sorted FOIA requests with the multi requests"""

        get = self.request.GET

        order = get.get('order', 'desc')
        field = get.get('field', 'date_submitted')

        updated_foia_requests = [f for f in foia_requests if f.updated]
        other_foia_requests = [f for f in foia_requests if not f.updated]

        if field == 'title':
            both = list(other_foia_requests) + list(multi_requests)
            both.sort(key=lambda x: x.title, reverse=(order != 'asc'))
            both = updated_foia_requests + both
        elif field == 'status':
            both = list(other_foia_requests) + list(multi_requests)
            both.sort(key=lambda x: x.status, reverse=(order != 'asc'))
            both = updated_foia_requests + both
        elif order == 'asc':
            both = list(updated_foia_requests) + list(other_foia_requests) + list(multi_requests)
        else:
            both = list(updated_foia_requests) + list(multi_requests) + list(other_foia_requests)

        return both

    def get_queryset(self):
        """Get FOIAs for this view"""
        unsorted = FOIARequest.objects.filter(user=self.request.user)
        multis = FOIAMultiRequest.objects.filter(user=self.request.user)
        sorted_requests = self.filter_sort_requests(unsorted, update_top=True)
        sorted_requests = self.merge_requests(sorted_requests, multis)
        return sorted_requests

    def get_context_data(self, **kwargs):
        context = super(MyList, self).get_context_data(**kwargs)

        get = self.request.GET
        form_fields = {
            'order': get.get('order', False),
            'sort': get.get('field', False),
            'status': get.get('status', False),
            'agency': get.get('agency', False),
            'jurisdiction': get.get('jurisdiction', False),
            'user': get.get('user', False),
            'tags': get.get('tags', False)
        }
        form_initials = {}
        for key, value in form_fields.iteritems():
            if value:
                form_initials.update({key: value})
        
        context['title'] = 'My FOI Requests'
        context['form'] = MyListFilterForm(initial=form_initials)
        return context


@class_view_decorator(login_required)
class ListFollowing(List):
    """List of all FOIA requests the user is following"""

    def get_queryset(self):
        """Get FOIAs for this view"""
        profile = self.request.user.get_profile()
        requests = FOIARequest.objects.get_viewable(self.request.user)
        return self.filter_sort_requests(requests.filter(followed_by=profile))

    def get_context_data(self, **kwargs):
        context = super(ListFollowing, self).get_context_data(**kwargs)
        return context

class Detail(DetailView):
    """Details of a single FOIA request as well
    as handling post actions for the request"""

    model = FOIARequest
    context_object_name = 'foia'
    
    def dispatch(self, request, *args, **kwargs):
        jurisdiction = self.kwargs['jurisdiction']
        jidx = self.kwargs['jidx']
        slug = self.kwargs['slug']
        idx = self.kwargs['idx']
        foia = get_foia(jurisdiction, jidx, slug, idx)
        if foia.status == 'started': 
            return redirect(
                'foia-draft',
                jurisdiction=jurisdiction,
                jidx=jidx,
                slug=slug,
                idx=idx
            )
        else:
            return super(Detail, self).dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        """Get the FOIA Request"""
        # pylint: disable=W0613
        jmodel = get_object_or_404(
            Jurisdiction,
            slug=self.kwargs['jurisdiction'],
            pk=self.kwargs['jidx']
        )
        foia = get_object_or_404(
            FOIARequest,
            jurisdiction=jmodel,
            slug=self.kwargs['slug'],
            pk=self.kwargs['idx']
        )
        if not foia.is_viewable(self.request.user):
            raise Http404()
        if foia.user == self.request.user:
            if foia.updated:
                foia.updated = False
                foia.save()
        return foia

    def get_context_data(self, **kwargs):
        """Add extra context data"""
        context = super(Detail, self).get_context_data(**kwargs)
        foia = context['foia']
        context['all_tags'] = Tag.objects.all()
        context['past_due'] = foia.date_due < datetime.now().date() if foia.date_due else False
        context['actions'] = foia.actions(self.request.user)
        context['choices'] = STATUS if self.request.user.is_staff or foia.status == 'started' else STATUS_NODRAFT
        context['stripe_pk'] = STRIPE_PUB_KEY
        return context

    def post(self, request, **kwargs):
        """Handle form submissions"""
        foia = self.get_object()
        actions = {
            'status': self._status,
            'tags': self._tags,
            'Submit': self._submit,
            'Follow Up': self._follow_up,
            'Get Advice': self._question,
            'Problem?': self._flag,
            'Appeal': self._appeal,
            'move_comm': move_comm,
            'delete_comm': delete_comm,
            'resend_comm': resend_comm
        }
        try:
            return actions[request.POST['action']](request, foia)
        except KeyError: # if submitting form from web page improperly
            return redirect(foia)
    
    def _submit(self, request, foia):
        """Submit request for user"""
        if not foia.user == request.user:
            messages.error(request, 'Only a request\'s owner may submit it.')
        if not request.user.get_profile().make_request():
            messages.error(request, 'You do not have any requests remaining. Please purchase more requests and then resubmit.')
        foia.submit()
        messages.success(request, 'Your request was submitted.')
        return redirect(foia)

    def _tags(self, request, foia):
        """Handle updating tags"""
        if foia.user == request.user or request.user.is_staff:
            foia.update_tags(request.POST.get('tags'))
        return redirect(foia)

    def _status(self, request, foia):
        """Handle updating status"""
        status = request.POST.get('status')
        old_status = foia.get_status_display()
        if foia.status not in ['started', 'submitted'] and ((foia.user == request.user and status in [s for s, _ in STATUS_NODRAFT]) or (request.user.is_staff and status in [s for s, _ in STATUS])):
            foia.status = status
            foia.save()
            
            subject = '%s changed the status of "%s" to %s' % (
                request.user.username,
                foia.title,
                foia.get_status_display()
            )
            args = {
                'request': foia,
                'old_status': old_status,
                'user': request.user
            }
            send_mail(
                subject,
                render_to_string('text/foia/status_change.txt', args),
                'info@muckrock.com',
                ['requests@muckrock.com'],
                fail_silently=False
            )
        return redirect(foia)

    def _follow_up(self, request, foia):
        """Handle submitting follow ups"""
        comm = request.POST.get('text', False)
        if foia.user == request.user and foia.status != 'started' and comm:
            save_foia_comm(
                request,
                foia,
                foia.user.get_full_name(),
                comm,
                'Your follow up has been sent.'
            )
        return redirect(foia)

    def _question(self, request, foia):
        """Handle asking a question"""
        q = request.POST.get('text', False)
        if foia.user == request.user:
            if q:
                title = 'Question about request: %s' % foia.title
                question = Question.objects.create(
                    user=request.user,
                    title=title,
                    slug=slugify(title),
                    foia=foia,
                    question=q,
                    date=datetime.now()
                )
                messages.success(request, 'Your question has been posted.')
                question.notify_new()
                return redirect(question)
            else:
                error_msg = 'There was an error while submitting your question.'
        else:
            error_msg = 'You may only ask questions about your own requests.'
        messages.error(request, error_msg)
        return redirect(foia)

    def _flag(self, request, foia):
        """Allow a user to notify us of a problem with the request"""
        if request.user.is_authenticated():
            args = {
                'request': foia,
                'user': request.user,
                'reason': request.POST.get('text')
            }
            send_mail(
                '[FLAG] Freedom of Information Request: %s' % foia.title,
                render_to_string('text/foia/flag.txt', args),
                'info@muckrock.com',
                ['requests@muckrock.com'],
                fail_silently=False
            )
            messages.info(request, 'Problem succesfully reported')
        return redirect(foia)

    def _appeal(self, request, foia):
        """Handle submitting an appeal"""
        if foia.user == request.user and foia.is_appealable():
            save_foia_comm(
                request,
                foia,
                foia.user.get_full_name(),
                request.POST.get('text'),
                'Appeal succesfully sent',
                appeal=True
            )
        return redirect(foia)

def redirect_old(request, jurisdiction, slug, idx, action):
    """Redirect old urls to new urls"""
    # pylint: disable=W0612
    # pylint: disable=W0613

    # some jurisdiction slugs changed, just ignore the jurisdiction slug passed in
    foia = get_object_or_404(FOIARequest, pk=idx)
    jurisdiction = foia.jurisdiction.slug
    jidx = foia.jurisdiction.pk

    if action == 'view':
        return redirect('/foi/%(jurisdiction)s-%(jidx)s/%(slug)s-%(idx)s/' % locals())

    if action == 'admin-fix':
        action = 'admin_fix'

    return redirect('/foi/%(jurisdiction)s-%(jidx)s/%(slug)s-%(idx)s/%(action)s/' % locals())

@user_passes_test(lambda u: u.is_staff)
def acronyms(request):
    """A page with all the acronyms explained"""
    status_dict = dict(STATUS)
    codes = [(acro, name, status_dict.get(status, ''), desc)
             for acro, (name, status, desc) in CODES.iteritems()]
    codes.sort()
    return render_to_response(
        'foia/acronyms.html',
        {'codes': codes},
        context_instance=RequestContext(request)
    )