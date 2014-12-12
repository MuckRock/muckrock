"""
Views for the FOIA application
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.http import Http404
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string
from django.template import RequestContext
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from datetime import datetime
import logging
import stripe

from muckrock.agency.models import Agency
from muckrock.foia.codes import CODES
from muckrock.foia.forms import \
    ListFilterForm, \
    MyListFilterForm
from muckrock.foia.models import \
    FOIARequest, \
    FOIAMultiRequest, \
    STATUS
from muckrock.foia.views.comms import move_comm, delete_comm, save_foia_comm, resend_comm
from muckrock.foia.views.composers import get_foia
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.qanda.models import Question
from muckrock.settings import STRIPE_PUB_KEY, STRIPE_SECRET_KEY
from muckrock.tags.models import Tag
from muckrock.views import class_view_decorator

# pylint: disable=R0901

logger = logging.getLogger(__name__)
stripe.api_key = STRIPE_SECRET_KEY
STATUS_NODRAFT = [st for st in STATUS if st != ('started', 'Draft')]

class List(ListView):
    """Base list view for other list views to inherit from"""

    def filter_sort_requests(self, foia_requests):
        """Sorts the FOIA requests"""
        get = self.request.GET
        order = get.get('order', 'desc')
        sort = get.get('sort', 'date_submitted')
        list_filter = {
            'status': get.get('status', False),
            'agency': get.get('agency', False),
            'jurisdiction': get.get('jurisdiction', False),
            'user': get.get('user', False),
            'tags': get.get('tags', False)
        }

        # TODO: handle a list of tags
        for key, value in list_filter.iteritems():
            if value:
                print value
                if key == 'status':
                    foia_requests = foia_requests.filter(status=value)
                elif key == 'agency':
                    agency_obj = get_object_or_404(Agency, id=value)
                    foia_requests = foia_requests.filter(agency=agency_obj)
                elif key == 'jurisdiction':
                    value = value.split(',')
                    juris_obj = get_object_or_404(Jurisdiction, id=value[0])
                    foia_requests = foia_requests.filter(jurisdiction=juris_obj)
                elif key == 'user':
                    user_obj = get_object_or_404(User, username=value)
                    foia_requests = foia_requests.filter(user=user_obj)
                # elif key == 'tags':
                    # foia_requests = foia_requests.filter(tags__slug=value)


        # Handle extra cases by resorting to default values
        if order not in ['asc', 'desc']:
            order = 'desc'
        if sort not in ['title', 'date_submitted', 'times_viewed']:
            sort = 'date_submitted'
        ob_field = '-' + sort if order == 'desc' else sort
        foia_requests = foia_requests.order_by(ob_field)

        return foia_requests

    def get_paginate_by(self, queryset):
        return 15

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
        """Handle updating read status"""
        try:
            post = request.POST
            foia_pks = post.getlist('foia')
            if post.get('submit') == 'Mark as Read':
                self.set_read_status(foia_pks, False)
            elif post.get('submit') == 'Mark as Unread':
                self.set_read_status(foia_pks, True)
            elif post.get('submit') == 'Mark All as Read':
                foia_requests = FOIARequest.objects.filter(user=self.request.user, updated=True)
                all_unread = [foia.pk for foia in foia_requests]
                self.set_read_status(all_unread, False)
        except FOIARequest.DoesNotExist:
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
        sorted_requests = self.filter_sort_requests(unsorted)
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

# pylint: disable=no-self-use
class Detail(DetailView):
    """Details of a single FOIA request as well
    as handling post actions for the request"""

    model = FOIARequest
    context_object_name = 'foia'

    def dispatch(self, request, *args, **kwargs):
        """If request is a draft, then redirect to drafting interface"""
        if request.POST:
            return self.post(request)
        foia = get_foia(
            self.kwargs['jurisdiction'],
            self.kwargs['jidx'],
            self.kwargs['slug'],
            self.kwargs['idx']
        )
        if foia.status == 'started':
            return redirect(
                'foia-draft',
                jurisdiction=self.kwargs['jurisdiction'],
                jidx=self.kwargs['jidx'],
                slug=self.kwargs['slug'],
                idx=self.kwargs['idx']
            )
        else:
            return super(Detail, self).dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        """Get the FOIA Request"""
        # pylint: disable=W0613
        foia = get_foia(
            self.kwargs['jurisdiction'],
            self.kwargs['jidx'],
            self.kwargs['slug'],
            self.kwargs['idx']
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
        user = self.request.user
        is_past_due = foia.date_due < datetime.now().date() if foia.date_due else False
        context['all_tags'] = Tag.objects.all()
        context['past_due'] = is_past_due
        context['admin_actions'] = foia.admin_actions(user)
        context['user_actions'] = foia.user_actions(user)
        context['noncontextual_request_actions'] = foia.noncontextual_request_actions(user)
        context['contextual_request_actions'] = foia.contextual_request_actions(user)
        context['choices'] = STATUS if user.is_staff or foia.status == 'started' else STATUS_NODRAFT
        context['stripe_pk'] = STRIPE_PUB_KEY
        return context

    def post(self, request):
        """Handle form submissions"""
        foia = self.get_object()
        actions = {
            'status': self._status,
            'tags': self._tags,
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

    def _tags(self, request, foia):
        """Handle updating tags"""
        if foia.user == request.user or request.user.is_staff:
            foia.update_tags(request.POST.get('tags'))
        return redirect(foia)

    # pylint: disable=line-too-long
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
        text = request.POST.get('text', False)
        if foia.user == request.user and foia.status != 'started' and text:
            save_foia_comm(
                request,
                foia,
                foia.user.get_full_name(),
                text,
                'Your follow up has been sent.'
            )
        return redirect(foia)

    def _question(self, request, foia):
        """Handle asking a question"""
        text = request.POST.get('text')
        if foia.user == request.user and text:
            title = 'Question about request: %s' % foia.title
            question = Question.objects.create(
                user=request.user,
                title=title,
                slug=slugify(title),
                foia=foia,
                question=text,
                date=datetime.now()
            )
            messages.success(request, 'Your question has been posted.')
            question.notify_new()
            return redirect(question)

        return redirect(foia)

    def _flag(self, request, foia):
        """Allow a user to notify us of a problem with the request"""
        text = request.POST.get('text')
        if request.user.is_authenticated() and text:
            args = {
                'request': foia,
                'user': request.user,
                'reason': text
            }
            send_mail(
                '[FLAG] Freedom of Information Request: %s' % foia.title,
                render_to_string('text/foia/flag.txt', args),
                'info@muckrock.com',
                ['requests@muckrock.com'],
                fail_silently=False
            )
            messages.success(request, 'Problem succesfully reported')
        return redirect(foia)

    def _appeal(self, request, foia):
        """Handle submitting an appeal"""
        text = request.POST.get('text')
        if foia.user == request.user and foia.is_appealable() and text:
            save_foia_comm(
                request,
                foia,
                foia.user.get_full_name(),
                text,
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
        'staff/acronyms.html',
        {'codes': codes},
        context_instance=RequestContext(request)
    )
