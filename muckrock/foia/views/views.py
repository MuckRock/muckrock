"""
Views for the FOIA application
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template.defaultfilters import slugify
from django.template import RequestContext
from django.views.generic.detail import DetailView

from datetime import datetime
import logging
import stripe

from muckrock.foia.codes import CODES
from muckrock.foia.forms import RequestFilterForm, FOIAEmbargoForm, FOIAEstimatedCompletionDateForm
from muckrock.foia.models import \
    FOIARequest, \
    FOIAMultiRequest, \
    STATUS, END_STATUS
from muckrock.foia.views.comms import move_comm, delete_comm, save_foia_comm, resend_comm
from muckrock.qanda.models import Question
from muckrock.settings import STRIPE_PUB_KEY, STRIPE_SECRET_KEY
from muckrock.tags.models import Tag
from muckrock.task.models import Task, FlaggedTask, StatusChangeTask
from muckrock.views import class_view_decorator, MRFilterableListView

# pylint: disable=too-many-ancestors

logger = logging.getLogger(__name__)
stripe.api_key = STRIPE_SECRET_KEY
STATUS_NODRAFT = [st for st in STATUS if st != ('started', 'Draft')]

class RequestList(MRFilterableListView):
    """Base list view for other list views to inherit from"""
    model = FOIARequest
    title = 'Requests'
    template_name = 'lists/request_list.html'

    def get_filters(self):
        """Adds request-specific filter fields"""
        base_filters = super(RequestList, self).get_filters()
        new_filters = [{'field': 'status', 'lookup': 'exact'}]
        return base_filters + new_filters

    def get_context_data(self, **kwargs):
        """Changes filter_form to use RequestFilterForm instead of the default"""
        context = super(RequestList, self).get_context_data(**kwargs)
        filter_data = self.get_filter_data()
        context['filter_form'] = RequestFilterForm(initial=filter_data['filter_initials'])
        return context

    def get_queryset(self):
        """Limits requests to those visible by current user"""
        objects = super(RequestList, self).get_queryset()
        return objects.get_viewable(self.request.user)

@class_view_decorator(login_required)
class MyRequestList(RequestList):
    """View requests owned by current user"""

    template_name = 'lists/request_my_list.html'

    def post(self, request):
        """Handle updating read status"""
        try:
            post = request.POST
            foia_pks = post.getlist('foia')
            if post.get('submit') == 'Mark as Read':
                FOIARequest.objects.filter(pk__in=foia_pks).update(updated=False)
            elif post.get('submit') == 'Mark as Unread':
                FOIARequest.objects.filter(pk__in=foia_pks).update(updated=True)
            elif post.get('submit') == 'Mark All as Read':
                FOIARequest.objects.filter(user=self.request.user, updated=True)\
                                   .update(updated=False)
        except FOIARequest.DoesNotExist:
            pass
        return redirect('foia-mylist')

    def get_filters(self):
        """Removes the 'users' filter, because its _my_ requests"""
        filters = super(MyRequestList, self).get_filters()
        for filter_dict in filters:
            if 'user' in filter_dict.values():
                filters.pop(filters.index(filter_dict))
        return filters

    def get_queryset(self):
        """Gets multirequests as well, limits to just those by the current user"""
        single_req = FOIARequest.objects.filter(user=self.request.user)
        multi_req = FOIAMultiRequest.objects.filter(user=self.request.user)
        single_req = self.sort_list(self.filter_list(single_req))
        return list(single_req) + list(multi_req)

@class_view_decorator(login_required)
class FollowingRequestList(RequestList):
    """List of all FOIA requests the user is following"""
    def get_queryset(self):
        """Limits FOIAs to those followed by the current user"""
        objects = super(FollowingRequestList, self).get_queryset()
        profile = self.request.user.profile
        return objects.filter(followed_by=profile)

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
        foia = self.get_object()
        if foia.status == 'started':
            return redirect(
                'foia-draft',
                jurisdiction=foia.jurisdiction.slug,
                jidx=foia.jurisdiction.id,
                slug=foia.slug,
                idx=foia.id
            )
        else:
            return super(Detail, self).dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        """Get the FOIA Request"""
        foia = super(Detail, self).get_object(queryset)
        user = self.request.user
        if not foia.is_viewable(user):
            raise Http404()
        if foia.user == user:
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
        include_draft = user.is_staff or foia.status == 'started'
        context['all_tags'] = Tag.objects.all()
        context['past_due'] = is_past_due
        context['user_can_edit'] = foia.editable_by(user)
        context['embargo_form'] = FOIAEmbargoForm(initial={
            'permanent_embargo': foia.permanent_embargo,
            'date_embargo': foia.date_embargo
        })
        context['embargo_needs_date'] = foia.status in END_STATUS
        context['user_actions'] = foia.user_actions(user)
        context['noncontextual_request_actions'] = foia.noncontextual_request_actions(user)
        context['contextual_request_actions'] = foia.contextual_request_actions(user)
        context['status_choices'] = STATUS if include_draft else STATUS_NODRAFT
        context['show_estimated_date'] = foia.status not in ['submitted', 'ack', 'done', 'rejected']
        context['change_estimated_date'] = FOIAEstimatedCompletionDateForm(instance=foia)
        context['task_count'] = len(Task.objects.filter_by_foia(foia))
        context['open_tasks'] = Task.objects.get_unresolved().filter_by_foia(foia)
        context['stripe_pk'] = STRIPE_PUB_KEY
        context['sidebar_admin_url'] = reverse('admin:foia_foiarequest_change', args=(foia.pk,))
        if foia.sidebar_html:
            messages.info(self.request, foia.sidebar_html)
        return context

    def post(self, request):
        """Handle form submissions"""
        foia = self.get_object()
        actions = {
            'status': self._status,
            'tags': self._tags,
            'follow_up': self._follow_up,
            'question': self._question,
            'flag': self._flag,
            'appeal': self._appeal,
            'date_estimate': self._update_estimate,
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
        # pylint: disable=no-self-use
        if foia.editable_by(request.user) or request.user.is_staff:
            foia.update_tags(request.POST.get('tags'))
        return redirect(foia)

    # pylint: disable=line-too-long
    def _status(self, request, foia):
        """Handle updating status"""
        status = request.POST.get('status')
        old_status = foia.get_status_display()
        if foia.status not in ['started', 'submitted'] and \
                ((foia.editable_by(request.user) and status in [s for s, _ in STATUS_NODRAFT]) or
                 (request.user.is_staff and status in [s for s, _ in STATUS])):
            foia.status = status
            foia.save()

            StatusChangeTask.objects.create(
                user=request.user,
                old_status=old_status,
                foia=foia,
            )
        return redirect(foia)

    def _follow_up(self, request, foia):
        """Handle submitting follow ups"""
        text = request.POST.get('text', False)
        can_follow_up = foia.editable_by(request.user) or request.user.is_staff
        if can_follow_up and foia.status != 'started' and text:
            save_foia_comm(foia, foia.user.get_full_name(), text)
            messages.success(request, 'Your follow up has been sent.')
        return redirect(foia)

    def _question(self, request, foia):
        """Handle asking a question"""
        text = request.POST.get('text')
        if foia.editable_by(request.user) and text:
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
            FlaggedTask.objects.create(
                user=request.user,
                text=text,
                foia=foia)
            messages.success(request, 'Problem succesfully reported')
        return redirect(foia)

    def _appeal(self, request, foia):
        """Handle submitting an appeal"""
        text = request.POST.get('text')
        if foia.editable_by(request.user) and foia.is_appealable() and text:
            save_foia_comm(foia, foia.user.get_full_name(), text, appeal=True)
            messages.success(request, 'Appeal successfully sent.')
        return redirect(foia)

    def _update_estimate(self, request, foia):
        """Change the estimated completion date"""
        form = FOIAEstimatedCompletionDateForm(request.POST, instance=foia)
        if foia.editable_by(request.user):
            if form.is_valid():
                form.save()
                messages.success(request, 'Successfully changed the estimated completion date.')
            else:
                messages.error(request, 'Invalid date provided.')
        else:
            messages.error(request, 'You cannot do that, stop it.')
        return redirect(foia)

def redirect_old(request, jurisdiction, slug, idx, action):
    """Redirect old urls to new urls"""
    # pylint: disable=unused-variable
    # pylint: disable=unused-argument

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
