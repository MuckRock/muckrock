"""
Views for the FOIA application
"""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db.models import Prefetch
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template.defaultfilters import slugify
from django.template import RequestContext
from django.views.generic.detail import DetailView

from actstream.models import following
from datetime import datetime, timedelta
import json
import logging

from muckrock.accounts.models import Notification
from muckrock.agency.forms import AgencyForm
from muckrock.crowdfund.forms import CrowdfundForm
from muckrock.foia.codes import CODES
from muckrock.foia.forms import (
    RequestFilterForm,
    FOIAEmbargoForm,
    FOIANoteForm,
    FOIAEstimatedCompletionDateForm,
    FOIAAccessForm,
    )
from muckrock.foia.models import (
    FOIARequest,
    FOIAMultiRequest,
    RawEmail,
    STATUS,
    END_STATUS,
    )
from muckrock.foia.views.composers import get_foia
from muckrock.foia.views.comms import (
        move_comm,
        delete_comm,
        resend_comm,
        change_comm_status,
        )
from muckrock.jurisdiction.models import Appeal
from muckrock.jurisdiction.forms import AppealForm
from muckrock.project.forms import ProjectManagerForm
from muckrock.qanda.models import Question
from muckrock.qanda.forms import QuestionForm
from muckrock.tags.models import Tag
from muckrock.task.models import Task, FlaggedTask, StatusChangeTask
from muckrock.utils import new_action
from muckrock.views import class_view_decorator, MRFilterableListView

# pylint: disable=too-many-ancestors

logger = logging.getLogger(__name__)
STATUS_NODRAFT = [st for st in STATUS if st != ('started', 'Draft')]


class RequestList(MRFilterableListView):
    """Base list view for other list views to inherit from"""
    model = FOIARequest
    title = 'Requests'
    template_name = 'lists/request_list.html'
    default_sort = 'title'

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
        objects = objects.select_related('jurisdiction')
        objects = objects.only(
                'title', 'slug', 'status', 'date_submitted', 'date_due',
                'date_updated', 'date_processing', 'jurisdiction__slug')
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
        single_req = (FOIARequest.objects
                .filter(user=self.request.user)
                .select_related('jurisdiction')
                .prefetch_related('communications')
                )
        multi_req = FOIAMultiRequest.objects.filter(user=self.request.user)
        single_req = self.sort_list(self.filter_list(single_req))
        return list(single_req) + list(multi_req)


@class_view_decorator(login_required)
class FollowingRequestList(RequestList):
    """List of all FOIA requests the user is following"""
    def get_queryset(self):
        """Limits FOIAs to those followed by the current user"""
        objects = following(self.request.user, FOIARequest)
        # actstream returns a list of objects, so we have to turn it into a queryset
        pk_list = [_object.pk for _object in objects if _object]
        objects = FOIARequest.objects.filter(pk__in=pk_list)
        objects = objects.select_related('jurisdiction')
        # now we filter and sort the list like in the parent class
        objects = self.filter_list(objects)
        objects = self.sort_list(objects)
        # finally, we can only show requests visible to that user
        return objects.get_viewable(self.request.user)


class ProcessingRequestList(RequestList):
    """List all of the currently processing FOIA requests."""
    template_name = 'lists/request_processing_list.html'
    default_sort = 'date_processing'

    def dispatch(self, *args, **kwargs):
        """Only staff can see the list of processing requests."""
        if not self.request.user.is_staff:
            raise Http404()
        return super(ProcessingRequestList, self).dispatch(*args, **kwargs)

    def filter_list(self, objects):
        """Gets all processing requests"""
        objects = super(ProcessingRequestList, self).filter_list(objects)
        return objects.filter(status='submitted')

    def get_filters(self):
        """Removes the 'status' filter, because its only processing requests"""
        filters = super(ProcessingRequestList, self).get_filters()
        for filter_dict in filters:
            if 'status' in filter_dict.values():
                filters.pop(filters.index(filter_dict))
        return filters

    def get_queryset(self):
        """Apply select and prefetch related"""
        objects = super(ProcessingRequestList, self).get_queryset()
        return (objects
                .prefetch_related('communications'))


# pylint: disable=no-self-use
class Detail(DetailView):
    """Details of a single FOIA request as well
    as handling post actions for the request"""

    model = FOIARequest
    context_object_name = 'foia'

    def __init__(self, *args, **kwargs):
        self._obj = None
        super(Detail, self).__init__(*args, **kwargs)

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
        # pylint: disable=unused-argument
        # pylint: disable=unsubscriptable-object
        # this is called twice in dispatch, so cache to not actually run twice
        if self._obj:
            return self._obj

        foia = get_foia(
            self.kwargs['jurisdiction'],
            self.kwargs['jidx'],
            self.kwargs['slug'],
            self.kwargs['idx'],
            select_related=(
                'agency',
                'agency__jurisdiction',
                'crowdfund',
                'jurisdiction',
                'jurisdiction__parent',
                'jurisdiction__parent__parent',
                'user',
                'user__profile',
                ),
            prefetch_related=(
                'communications',
                'communications__files',
                Prefetch('communications__rawemail', RawEmail.objects.defer('raw_email')),
                ),
        )
        valid_access_key = self.request.GET.get('key') == foia.access_key
        has_perm = self.request.user.has_perm('foia.view_foiarequest', foia)
        if not has_perm and not valid_access_key:
            raise Http404()
        self._obj = foia
        return foia

    def get_context_data(self, **kwargs):
        """Add extra context data"""
        context = super(Detail, self).get_context_data(**kwargs)
        foia = context['foia']
        user = self.request.user
        user_can_edit = user.has_perm('foia.change_foiarequest', foia)
        user_can_embargo = user.has_perm('foia.embargo_foiarequest', foia)
        is_past_due = foia.date_due < datetime.now().date() if foia.date_due else False
        include_draft = user.is_staff or foia.status == 'started'
        context['all_tags'] = Tag.objects.all()
        context['past_due'] = is_past_due
        context['user_can_edit'] = user_can_edit
        context['user_can_pay'] = user_can_edit and foia.is_payable()
        context['embargo'] = {
            'show': user_can_embargo or foia.embargo,
            'edit': user_can_embargo,
            'add': user_can_embargo,
            'remove': user_can_edit and foia.embargo,
        }
        context['embargo_form'] = FOIAEmbargoForm(initial={
            'permanent_embargo': foia.permanent_embargo,
            'date_embargo': foia.date_embargo
        })
        context['note_form'] = FOIANoteForm()
        context['access_form'] = FOIAAccessForm()
        context['question_form'] = QuestionForm(user=user, initial={'foia': foia})
        context['crowdfund_form'] = CrowdfundForm(initial={
            'name': u'Crowdfund Request: %s' % unicode(foia),
            'description': 'Help cover the request fees needed to free these docs!',
            'payment_required': foia.get_stripe_amount(),
            'date_due': datetime.now() + timedelta(30),
            'foia': foia
        })
        context['embargo_needs_date'] = foia.status in END_STATUS
        context['user_actions'] = foia.user_actions(user)
        context['contextual_request_actions'] = \
                foia.contextual_request_actions(user, user_can_edit)
        context['status_choices'] = STATUS if include_draft else STATUS_NODRAFT
        context['show_estimated_date'] = foia.status not in ['submitted', 'ack', 'done', 'rejected']
        context['change_estimated_date'] = FOIAEstimatedCompletionDateForm(instance=foia)

        all_tasks = Task.objects.filter_by_foia(foia, user)
        open_tasks = [task for task in all_tasks if not task.resolved]
        context['task_count'] = len(all_tasks)
        context['open_task_count'] = len(open_tasks)
        context['open_tasks'] = open_tasks
        context['stripe_pk'] = settings.STRIPE_PUB_KEY
        context['sidebar_admin_url'] = reverse('admin:foia_foiarequest_change', args=(foia.pk,))
        context['is_thankable'] = self.request.user.has_perm(
                'foia.thank_foiarequest', foia)
        context['files'] = foia.files.all()[:50]
        if foia.sidebar_html:
            messages.info(self.request, foia.sidebar_html)
        return context

    def get(self, request, *args, **kwargs):
        """Mark any unread notifications for this object as read."""
        user = request.user
        if user.is_authenticated():
            foia = self.get_object()
            notifications = Notification.objects.for_user(user).for_object(foia).get_unread()
            for notification in notifications:
                notification.mark_read()
        return super(Detail, self).get(request, *args, **kwargs)

    def post(self, request):
        """Handle form submissions"""
        foia = self.get_object()
        actions = {
            'status': self._status,
            'tags': self._tags,
            'projects': self._projects,
            'follow_up': self._follow_up,
            'thanks': self._thank,
            'question': self._question,
            'add_note': self._add_note,
            'flag': self._flag,
            'appeal': self._appeal,
            'date_estimate': self._update_estimate,
            'status_comm': change_comm_status,
            'move_comm': move_comm,
            'delete_comm': delete_comm,
            'resend_comm': resend_comm,
            'generate_key': self._generate_key,
            'grant_access': self._grant_access,
            'revoke_access': self._revoke_access,
            'demote': self._demote_editor,
            'promote': self._promote_viewer,
            'update_new_agency': self._update_new_agency,
        }
        try:
            return actions[request.POST['action']](request, foia)
        except KeyError: # if submitting form from web page improperly
            return redirect(foia)

    def _tags(self, request, foia):
        """Handle updating tags"""
        # pylint: disable=no-self-use
        if request.user.has_perm('foia.change_foiarequest', foia):
            foia.update_tags(request.POST.get('tags'))
        return redirect(foia)

    def _projects(self, request, foia):
        """Handle updating projects"""
        form = ProjectManagerForm(request.POST)
        has_perm = request.user.has_perm('foia.change_foiarequest', foia)
        if has_perm and form.is_valid():
            projects = form.cleaned_data['projects']
            foia.projects = projects
        return redirect(foia)

    def _status(self, request, foia):
        """Handle updating status"""
        status = request.POST.get('status')
        old_status = foia.get_status_display()
        has_perm = request.user.has_perm('foia.change_foiarequest', foia)
        user_editable = has_perm and status in [s for s, _ in STATUS_NODRAFT]
        staff_editable = request.user.is_staff and status in [s for s, _ in STATUS]
        if foia.status not in ['started', 'submitted'] and (user_editable or staff_editable):
            foia.status = status
            foia.save(comment='status updated')
            StatusChangeTask.objects.create(
                user=request.user,
                old_status=old_status,
                foia=foia,
            )
        return redirect(foia)

    def _question(self, request, foia):
        """Handle asking a question"""
        text = request.POST.get('text')
        has_perm = request.user.has_perm('foia.change_foiarequest', foia)
        if has_perm and text:
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
            return redirect(question)
        return redirect(foia)

    def _add_note(self, request, foia):
        """Adds a note to the request"""
        note_form = FOIANoteForm(request.POST)
        has_perm = request.user.has_perm('foia.change_foiarequest', foia)
        if has_perm and note_form.is_valid():
            foia_note = note_form.save(commit=False)
            foia_note.foia = foia
            foia_note.author = request.user
            foia_note.datetime = datetime.now()
            foia_note.save()
            logging.info('%s added %s to %s', foia_note.author, foia_note, foia_note.foia)
            messages.success(request, 'Your note is attached to the request.')
        return redirect(foia)

    def _flag(self, request, foia):
        """Allow a user to notify us of a problem with the request"""
        text = request.POST.get('text')
        has_perm = request.user.has_perm('foia.flag_foiarequest', foia)
        if has_perm and text:
            FlaggedTask.objects.create(
                user=request.user,
                text=text,
                foia=foia)
            messages.success(request, 'Problem succesfully reported')
            new_action(request.user, 'flagged', target=foia)
        return redirect(foia)

    def _follow_up(self, request, foia):
        """Handle submitting follow ups"""
        success_msg = 'Your follow up has been sent.'
        has_perm = request.user.has_perm('foia.followup_foiarequest', foia)
        comm_sent = self._new_comm(request, foia, has_perm, success_msg)
        if comm_sent:
            new_action(request.user, 'followed up on', target=foia)
        return redirect(foia)

    def _thank(self, request, foia):
        """Handle submitting a thank you follow up"""
        success_msg = 'Your thank you has been sent.'
        has_perm = request.user.has_perm('foia.thank_foiarequest', foia)
        comm_sent = self._new_comm(
                request, foia, has_perm, success_msg, thanks=True)
        if comm_sent:
            new_action(request.user, verb='thanked', target=foia.agency)
        return redirect(foia)

    def _appeal(self, request, foia):
        """Handle submitting an appeal, then create an Appeal from the returned communication."""
        form = AppealForm(request.POST)
        has_perm = request.user.has_perm('foia.appeal_foiarequest', foia)
        if not has_perm:
            messages.error(request, 'You do not have permission to submit an appeal.')
            return redirect(foia)
        if not form.is_valid():
            messages.error(request, 'You did not submit an appeal.')
            return redirect(foia)
        communication = foia.appeal(form.cleaned_data['text'])
        base_language = form.cleaned_data['base_language']
        appeal = Appeal.objects.create(communication=communication)
        appeal.base_language.set(base_language)
        new_action(request.user, 'appealed', target=foia)
        messages.success(request, 'Your appeal has been sent.')
        return redirect(foia)

    def _new_comm(self, request, foia, test, success_msg, appeal=False, thanks=False):
        """Helper function for sending a new comm"""
        # pylint: disable=too-many-arguments
        text = request.POST.get('text')
        comm_sent = False
        if text and test:
            foia.create_out_communication(
                    from_user=foia.user,
                    text=text,
                    thanks=thanks,
                    )
            foia.submit(appeal=appeal, thanks=thanks)
            messages.success(request, success_msg)
            comm_sent = True
        return comm_sent

    def _update_estimate(self, request, foia):
        """Change the estimated completion date"""
        form = FOIAEstimatedCompletionDateForm(request.POST, instance=foia)
        if request.user.has_perm('foia.change_foiarequest', foia):
            if form.is_valid():
                form.save()
                messages.success(request, 'Successfully changed the estimated completion date.')
            else:
                messages.error(request, 'Invalid date provided.')
        else:
            messages.error(request, 'You cannot do that, stop it.')
        return redirect(foia)

    def _update_new_agency(self, request, foia):
        """Update the new agency"""
        form = AgencyForm(request.POST, instance=foia.agency)
        if request.user.has_perm('foia.change_foiarequest', foia):
            if form.is_valid():
                form.save()
                messages.success(request, 'Agency info saved. Thanks for your help!')
            else:
                messages.success(request, 'The data was invalid! Try again.')
        else:
            messages.error(request, 'You cannot do that, stop it.')
        return redirect(foia)

    def _generate_key(self, request, foia):
        """Generate and return an access key, with support for AJAX."""
        if not request.user.has_perm('foia.change_foiarequest', foia):
            if request.is_ajax():
                return PermissionDenied
            else:
                return redirect(foia)
        else:
            key = foia.generate_access_key()
            if request.is_ajax():
                return HttpResponse(json.dumps({'key': key}), 'application/json')
            else:
                messages.success(request, 'New private link created.')
                return redirect(foia)

    def _grant_access(self, request, foia):
        """Grant editor access to the specified users."""
        form = FOIAAccessForm(request.POST)
        has_perm = request.user.has_perm('foia.change_foiarequest', foia)
        if not has_perm or not form.is_valid():
            return redirect(foia)
        access = form.cleaned_data['access']
        users = form.cleaned_data['users']
        if access == 'edit' and users:
            for user in users:
                foia.add_editor(user)
        if access == 'view' and users:
            for user in users:
                foia.add_viewer(user)
        if len(users) > 1:
            success_msg = '%d people can now %s this request.' % (len(users), access)
        else:
            success_msg = '%s can now %s this request.' % (users[0].first_name, access)
        messages.success(request, success_msg)
        return redirect(foia)

    def _revoke_access(self, request, foia):
        """Revoke access from a user."""
        user_pk = request.POST.get('user')
        user = User.objects.get(pk=user_pk)
        has_perm = request.user.has_perm('foia.change_foiarequest', foia)
        if has_perm and user:
            if foia.has_editor(user):
                foia.remove_editor(user)
            elif foia.has_viewer(user):
                foia.remove_viewer(user)
            messages.success(request, '%s no longer has access to this request.' % user.first_name)
        return redirect(foia)

    def _demote_editor(self, request, foia):
        """Demote user from editor access to viewer access"""
        user_pk = request.POST.get('user')
        user = User.objects.get(pk=user_pk)
        has_perm = request.user.has_perm('foia.change_foiarequest', foia)
        if has_perm and user:
            foia.demote_editor(user)
            messages.success(request, '%s can now only view this request.' % user.first_name)
        return redirect(foia)

    def _promote_viewer(self, request, foia):
        """Promote user from viewer access to editor access"""
        user_pk = request.POST.get('user')
        user = User.objects.get(pk=user_pk)
        has_perm = request.user.has_perm('foia.change_foiarequest', foia)
        if has_perm and user:
            foia.promote_viewer(user)
            messages.success(request, '%s can now edit this request.' % user.first_name)
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
