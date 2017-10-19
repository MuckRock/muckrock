"""
Views for the FOIA application
"""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db.models import Prefetch, Count
from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.template.defaultfilters import slugify
from django.views.generic import DetailView, TemplateView

from actstream.models import following
from datetime import datetime, timedelta
import json
import logging

from muckrock.accounts.models import Notification
from muckrock.agency.forms import AgencyForm
from muckrock.agency.models import Agency
from muckrock.communication.models import (
        EmailCommunication,
        FaxCommunication,
        WebCommunication,
        )
from muckrock.crowdfund.forms import CrowdfundForm
from muckrock.foia.codes import CODES
from muckrock.foia.filters import (
    FOIARequestFilterSet,
    MyFOIARequestFilterSet,
    MyFOIAMultiRequestFilterSet,
    ProcessingFOIARequestFilterSet,
    AgencyFOIARequestFilterSet,
)
from muckrock.foia.forms import (
    FOIAEmbargoForm,
    FOIANoteForm,
    FOIAEstimatedCompletionDateForm,
    FOIAAccessForm,
    FOIAAgencyReplyForm,
    FOIAAdminFixForm,
    )
from muckrock.foia.models import (
    FOIARequest,
    FOIACommunication,
    FOIAMultiRequest,
    STATUS,
    END_STATUS,
    )
from muckrock.foia.views.composers import get_foia
from muckrock.foia.views.comms import (
        move_comm,
        delete_comm,
        save_foia_comm,
        resend_comm,
        change_comm_status,
        )
from muckrock.jurisdiction.models import Appeal
from muckrock.jurisdiction.forms import AppealForm
from muckrock.message.email import TemplateEmail
from muckrock.news.models import Article
from muckrock.project.forms import ProjectManagerForm
from muckrock.project.models import Project
from muckrock.qanda.models import Question
from muckrock.qanda.forms import QuestionForm
from muckrock.tags.models import Tag
from muckrock.task.models import Task, FlaggedTask, StatusChangeTask, ResponseTask
from muckrock.utils import new_action
from muckrock.views import class_view_decorator, MRFilterListView, MRSearchFilterListView

# pylint: disable=too-many-ancestors

logger = logging.getLogger(__name__)
STATUS_NODRAFT = [st for st in STATUS if st != ('started', 'Draft')]
AGENCY_STATUS = [
    ('processed', 'Further Response Coming'),
    ('fix', 'Fix Required'),
    ('payment', 'Payment Required'),
    ('rejected', 'Rejected'),
    ('no_docs', 'No Responsive Documents'),
    ('done', 'Completed'),
    ('partial', 'Partially Completed'),
    ]


class RequestExploreView(TemplateView):
    """Provides a top-level page for exploring interesting requests."""
    template_name = 'foia/explore.html'

    def get_context_data(self, **kwargs):
        """Adds interesting data to the context for rendering."""
        context = super(RequestExploreView, self).get_context_data(**kwargs)
        user = self.request.user
        visible_requests = FOIARequest.objects.get_viewable(user)
        context['top_agencies'] = (
            Agency.objects
            .get_approved()
            .annotate(foia_count=Count('foiarequest'))
            .order_by('-foia_count')
        )[:9]
        context['featured_requests'] = (
            visible_requests
            .filter(featured=True)
            .order_by('featured')
            .select_related_view()
        )
        context['recent_news'] = (
            Article.objects
            .get_published()
            .annotate(foia_count=Count('foias'))
            .exclude(foia_count__lt=2)
            .exclude(foia_count__gt=9)
            .prefetch_related(
                'authors',
                'foias',
                'foias__user',
                'foias__user__profile',
                'foias__agency',
                'foias__agency__jurisdiction',
                'foias__jurisdiction__parent__parent')
            .order_by('-pub_date')
        )[:3]
        context['featured_projects'] = (
            Project.objects
            .get_visible(user)
            .filter(featured=True)
            .prefetch_related(
                'requests',
                'requests__user',
                'requests__user__profile',
                'requests__agency',
                'requests__agency__jurisdiction',
                'requests__jurisdiction__parent__parent')
        )
        context['recently_completed'] = (
            visible_requests
            .get_done()
            .order_by('-date_done', 'pk')
            .select_related_view()
            .get_public_file_count(limit=5))
        context['recently_rejected'] = (
            visible_requests
            .filter(status__in=['rejected', 'no_docs'])
            .order_by('-date_updated', 'pk')
            .select_related_view()
            .get_public_file_count(limit=5))
        return context


class RequestList(MRSearchFilterListView):
    """Base list view for other list views to inherit from"""
    model = FOIARequest
    filter_class = FOIARequestFilterSet
    title = 'All Requests'
    template_name = 'foia/list.html'
    default_sort = 'date_updated'
    default_order = 'desc'

    def get_queryset(self):
        """Limits requests to those visible by current user"""
        objects = super(RequestList, self).get_queryset()
        objects = objects.select_related_view()
        return objects.get_viewable(self.request.user)


@class_view_decorator(login_required)
class MyRequestList(RequestList):
    """View requests owned by current user"""
    filter_class = MyFOIARequestFilterSet
    title = 'Your Requests'
    template_name = 'foia/my_list.html'

    def get_queryset(self):
        """Limit to just requests owned by the current user."""
        queryset = super(MyRequestList, self).get_queryset()
        return queryset.filter(user=self.request.user)


@class_view_decorator(user_passes_test(lambda u: u.profile.acct_type == 'agency'))
class AgencyRequestList(RequestList):
    """View requests owned by current agency"""
    filter_class = AgencyFOIARequestFilterSet
    title = "Your Agency's Requests"
    template_name = 'foia/agency_list.html'

    def get_queryset(self):
        """Requests owned by the current agency that they can respond to."""
        queryset = super(AgencyRequestList, self).get_queryset()
        return queryset.filter(
                agency=self.request.user.profile.agency,
                status__in=(
                    'ack',
                    'processed',
                    'appealing',
                    'fix',
                    'payment',
                    'partial',
                    ),
                )


@class_view_decorator(login_required)
class MyMultiRequestList(MRFilterListView):
    """View requests owned by current user"""
    model = FOIAMultiRequest
    filter_class = MyFOIAMultiRequestFilterSet
    title = 'Multirequests'
    template_name = 'foia/multirequest_list.html'

    def dispatch(self, *args, **kwargs):
        """Basic users cannot access this view"""
        if self.request.user.is_authenticated and not self.request.user.profile.is_advanced():
            err_msg = (
                'Multirequests are a pro feature. '
                '<a href="%(settings_url)s">Upgrade today!</a>' % {
                    'settings_url': reverse('accounts')
                }
            )
            messages.error(self.request, err_msg)
            return redirect('foia-mylist')
        return super(MyMultiRequestList, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        """Limit to just requests owned by the current user."""
        queryset = super(MyMultiRequestList, self).get_queryset()
        return queryset.filter(user=self.request.user)


@class_view_decorator(login_required)
class FollowingRequestList(RequestList):
    """List of all FOIA requests the user is following"""
    title = 'Requests You Follow'

    def get_queryset(self):
        """Limits FOIAs to those followed by the current user"""
        queryset = super(FollowingRequestList, self).get_queryset()
        followed = [f.pk for f in following(self.request.user, FOIARequest)
                if f is not None]
        return queryset.filter(pk__in=followed)


class ProcessingRequestList(RequestList):
    """List all of the currently processing FOIA requests."""
    title = 'Processing Requests'
    filter_class = ProcessingFOIARequestFilterSet
    template_name = 'foia/processing_list.html'
    default_sort = 'date_processing'
    default_order = 'asc'

    def dispatch(self, *args, **kwargs):
        """Only staff can see the list of processing requests."""
        if not self.request.user.is_staff:
            raise Http404()
        return super(ProcessingRequestList, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        """Apply select and prefetch related"""
        objects = super(ProcessingRequestList, self).get_queryset()
        return objects.prefetch_related('communications').filter(status='submitted')


class FormError(Exception):
    """If a form fails validation"""


class Detail(DetailView):
    """Details of a single FOIA request as well
    as handling post actions for the request"""
    # pylint: disable=no-self-use

    model = FOIARequest
    context_object_name = 'foia'

    def __init__(self, *args, **kwargs):
        self._obj = None
        self.agency_reply_form = FOIAAgencyReplyForm()
        self.admin_fix_form = None
        super(Detail, self).__init__(*args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        """If request is a draft, then redirect to drafting interface"""
        foia = self.get_object()
        self.admin_fix_form = FOIAAdminFixForm(
                request=self.request,
                foia=self.get_object(),
                initial={
                    'email_or_fax': foia.email or foia.fax,
                    'subject': foia.default_subject(),
                    'other_emails': foia.get_other_emails(),
                    }
                )
        if request.POST:
            try:
                return self.post(request)
            except FormError:
                # if their is a form error, continue onto the GET path
                # and show the invalid form with errors displayed
                return self.get(request, *args, **kwargs)
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
                'communications__emails',
                'communications__faxes',
                'communications__mails',
                'communications__web_comms',
                Prefetch(
                    'communications__faxes',
                    FaxCommunication.objects.order_by('-sent_datetime'),
                    to_attr='reverse_faxes',
                    ),
                Prefetch(
                    'communications__emails',
                    EmailCommunication.objects.exclude(rawemail=None),
                    to_attr='raw_emails',
                    ),
                ),
        )
        valid_access_key = self.request.GET.get('key') == foia.access_key
        has_perm = foia.has_perm(self.request.user, 'view')
        if not has_perm and not valid_access_key:
            raise Http404()
        self._obj = foia
        return foia

    def get_context_data(self, **kwargs):
        """Add extra context data"""
        context = super(Detail, self).get_context_data(**kwargs)
        foia = context['foia']
        user = self.request.user
        user_can_edit = foia.has_perm(self.request.user, 'change')
        user_can_embargo = foia.has_perm(self.request.user, 'embargo')
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
        context['status_choices'] = STATUS if include_draft else STATUS_NODRAFT
        context['show_estimated_date'] = foia.status not in ['submitted', 'ack', 'done', 'rejected']
        context['change_estimated_date'] = FOIAEstimatedCompletionDateForm(instance=foia)

        if user_can_edit or user.is_staff:
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
        if self.request.user.is_authenticated():
            context['foia_cache_timeout'] = 0
        else:
            context['foia_cache_timeout'] = settings.DEFAULT_CACHE_TIMEOUT
        context['MAX_ATTACHMENT_NUM'] = settings.MAX_ATTACHMENT_NUM
        context['MAX_ATTACHMENT_SIZE'] = settings.MAX_ATTACHMENT_SIZE
        context['ALLOWED_FILE_MIMES'] = settings.ALLOWED_FILE_MIMES
        context['ALLOWED_FILE_EXTS'] = settings.ALLOWED_FILE_EXTS
        context['AWS_STORAGE_BUCKET_NAME'] = settings.AWS_STORAGE_BUCKET_NAME
        context['AWS_ACCESS_KEY_ID'] = settings.AWS_ACCESS_KEY_ID
        context['agency_status_choices'] = AGENCY_STATUS
        context['agency_reply_form'] = self.agency_reply_form
        context['admin_fix_form'] = self.admin_fix_form
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
            'contact_user': self._contact_user,
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
            'agency_reply': self._agency_reply,
        }
        try:
            return actions[request.POST['action']](request, foia)
        except KeyError: # if submitting form from web page improperly
            return redirect(foia)

    def _tags(self, request, foia):
        """Handle updating tags"""
        # pylint: disable=no-self-use
        if foia.has_perm(request.user, 'change'):
            foia.update_tags(request.POST.get('tags'))
        return redirect(foia.get_absolute_url() + '#')

    def _projects(self, request, foia):
        """Handle updating projects"""
        form = ProjectManagerForm(request.POST)
        has_perm = foia.has_perm(request.user, 'change')
        if has_perm and form.is_valid():
            projects = form.cleaned_data['projects']
            foia.projects = projects
        return redirect(foia.get_absolute_url() + '#')

    def _status(self, request, foia):
        """Handle updating status"""
        status = request.POST.get('status')
        old_status = foia.get_status_display()
        has_perm = foia.has_perm(request.user, 'change')
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
            response_tasks = ResponseTask.objects.filter(
                    resolved=False,
                    communication__foia=foia,
                    )
            for task in response_tasks:
                task.resolve(request.user)
        return redirect(foia.get_absolute_url() + '#')

    def _question(self, request, foia):
        """Handle asking a question"""
        text = request.POST.get('text')
        has_perm = foia.has_perm(request.user, 'change')
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
        return redirect(foia.get_absolute_url() + '#')

    def _add_note(self, request, foia):
        """Adds a note to the request"""
        note_form = FOIANoteForm(request.POST)
        has_perm = foia.has_perm(request.user, 'change')
        if has_perm and note_form.is_valid():
            foia_note = note_form.save(commit=False)
            foia_note.foia = foia
            foia_note.author = request.user
            foia_note.datetime = datetime.now()
            foia_note.save()
            logging.info('%s added %s to %s', foia_note.author, foia_note, foia_note.foia)
            messages.success(request, 'Your note is attached to the request.')
        return redirect(foia.get_absolute_url() + '#')

    def _flag(self, request, foia):
        """Allow a user to notify us of a problem with the request"""
        text = request.POST.get('text')
        has_perm = foia.has_perm(request.user, 'flag')
        if has_perm and text:
            FlaggedTask.objects.create(
                user=request.user,
                text=text,
                foia=foia)
            messages.success(request, 'Problem succesfully reported')
            new_action(request.user, 'flagged', target=foia)
        return redirect(foia.get_absolute_url() + '#')

    def _contact_user(self, request, foia):
        """Allow an admin to message the foia's owner"""
        text = request.POST.get('text')
        if request.user.is_staff and text:
            context = {
                    'text': text,
                    'foia_url': foia.user.profile.wrap_url(foia.get_absolute_url()),
                    'foia_title': foia.title,
                    }
            email = TemplateEmail(
                user=foia.user,
                extra_context=context,
                text_template='message/notification/contact_user.txt',
                html_template='message/notification/contact_user.html',
                subject='Message from MuckRock',
                )
            email.send(fail_silently=False)
            messages.success(request, 'Email sent to %s' % foia.user.email)
        return redirect(foia.get_absolute_url() + '#')

    def _follow_up(self, request, foia):
        """Handle submitting follow ups"""
        success_msg = 'Your follow up has been sent.'
        has_perm = foia.has_perm(request.user, 'followup')
        if request.user.is_staff:
            form = FOIAAdminFixForm(
                    request.POST,
                    request=request,
                    foia=foia,
                    )
            if form.is_valid():
                foia.update_address(form.cleaned_data['email_or_fax'])
                foia.cc_emails.set(form.cleaned_data['other_emails'])
                save_foia_comm(
                        foia,
                        form.cleaned_data['from_user'],
                        form.cleaned_data['comm'],
                        request.user,
                        snail=form.cleaned_data['snail_mail'],
                        subject=form.cleaned_data['subject'],
                        )
                messages.success(request, success_msg)
                new_action(request.user, 'followed up on', target=foia)
                return redirect(foia.get_absolute_url() + '#')
            else:
                self.admin_fix_form = form
                raise FormError
        else:
            comm_sent = self._new_comm(request, foia, has_perm, success_msg)
            if comm_sent:
                new_action(request.user, 'followed up on', target=foia)
            return redirect(foia.get_absolute_url() + '#')

    def _thank(self, request, foia):
        """Handle submitting a thank you follow up"""
        success_msg = 'Your thank you has been sent.'
        has_perm = foia.has_perm(request.user, 'thank')
        comm_sent = self._new_comm(
                request, foia, has_perm, success_msg, thanks=True)
        if comm_sent:
            new_action(request.user, verb='thanked', target=foia.agency)
        return redirect(foia.get_absolute_url() + '#')

    def _appeal(self, request, foia):
        """Handle submitting an appeal, then create an Appeal from the returned communication."""
        form = AppealForm(request.POST)
        has_perm = foia.has_perm(request.user, 'appeal')
        if not has_perm:
            messages.error(request, 'You do not have permission to submit an appeal.')
            return redirect(foia.get_absolute_url() + '#')
        if not form.is_valid():
            messages.error(request, 'You did not submit an appeal.')
            return redirect(foia.get_absolute_url() + '#')
        communication = foia.appeal(form.cleaned_data['text'], request.user)
        base_language = form.cleaned_data['base_language']
        appeal = Appeal.objects.create(communication=communication)
        appeal.base_language.set(base_language)
        new_action(request.user, 'appealed', target=foia)
        messages.success(request, 'Your appeal has been sent.')
        return redirect(foia.get_absolute_url() + '#')

    def _new_comm(self, request, foia, test, success_msg, appeal=False, thanks=False):
        """Helper function for sending a new comm"""
        # pylint: disable=too-many-arguments
        text = request.POST.get('text')
        comm_sent = False
        if text and test:
            save_foia_comm(
                    foia,
                    request.user,
                    text,
                    request.user,
                    appeal=appeal,
                    thanks=thanks,
                    )
            messages.success(request, success_msg)
            comm_sent = True
        return comm_sent

    def _update_estimate(self, request, foia):
        """Change the estimated completion date"""
        form = FOIAEstimatedCompletionDateForm(request.POST, instance=foia)
        if foia.has_perm(request.user, 'change'):
            if form.is_valid():
                form.save()
                messages.success(request, 'Successfully changed the estimated completion date.')
            else:
                messages.error(request, 'Invalid date provided.')
        else:
            messages.error(request, 'You cannot do that, stop it.')
        return redirect(foia.get_absolute_url() + '#')

    def _update_new_agency(self, request, foia):
        """Update the new agency"""
        form = AgencyForm(request.POST, instance=foia.agency)
        if foia.has_perm(request.user, 'change'):
            if form.is_valid():
                form.save()
                messages.success(request, 'Agency info saved. Thanks for your help!')
            else:
                messages.success(request, 'The data was invalid! Try again.')
        else:
            messages.error(request, 'You cannot do that, stop it.')
        return redirect(foia.get_absolute_url() + '#')

    def _generate_key(self, request, foia):
        """Generate and return an access key, with support for AJAX."""
        if not foia.has_perm(request.user, 'change'):
            if request.is_ajax():
                return PermissionDenied
            else:
                return redirect(foia.get_absolute_url() + '#')
        else:
            key = foia.generate_access_key()
            if request.is_ajax():
                return HttpResponse(json.dumps({'key': key}), 'application/json')
            else:
                messages.success(request, 'New private link created.')
                return redirect(foia.get_absolute_url() + '#')

    def _grant_access(self, request, foia):
        """Grant editor access to the specified users."""
        form = FOIAAccessForm(request.POST)
        has_perm = foia.has_perm(request.user, 'change')
        if not has_perm or not form.is_valid():
            return redirect(foia.get_absolute_url() + '#')
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
        return redirect(foia.get_absolute_url() + '#')

    def _revoke_access(self, request, foia):
        """Revoke access from a user."""
        user_pk = request.POST.get('user')
        user = User.objects.get(pk=user_pk)
        has_perm = foia.has_perm(request.user, 'change')
        if has_perm and user:
            if foia.has_editor(user):
                foia.remove_editor(user)
            elif foia.has_viewer(user):
                foia.remove_viewer(user)
            messages.success(request, '%s no longer has access to this request.' % user.first_name)
        return redirect(foia.get_absolute_url() + '#')

    def _demote_editor(self, request, foia):
        """Demote user from editor access to viewer access"""
        user_pk = request.POST.get('user')
        user = User.objects.get(pk=user_pk)
        has_perm = foia.has_perm(request.user, 'change')
        if has_perm and user:
            foia.demote_editor(user)
            messages.success(request, '%s can now only view this request.' % user.first_name)
        return redirect(foia.get_absolute_url() + '#')

    def _promote_viewer(self, request, foia):
        """Promote user from viewer access to editor access"""
        user_pk = request.POST.get('user')
        user = User.objects.get(pk=user_pk)
        has_perm = foia.has_perm(request.user, 'change')
        if has_perm and user:
            foia.promote_viewer(user)
            messages.success(request, '%s can now edit this request.' % user.first_name)
        return redirect(foia.get_absolute_url() + '#')

    def _agency_reply(self, request, foia):
        """Agency reply directly through the site"""
        form = FOIAAgencyReplyForm(request.POST)
        if form.is_valid():
            comm = FOIACommunication.objects.create(
                    foia=foia,
                    from_user=request.user,
                    to_user=foia.user,
                    response=True,
                    date=datetime.now(),
                    communication=form.cleaned_data['reply'],
                    status=form.cleaned_data['status'],
                    )
            WebCommunication.objects.create(
                    communication=comm,
                    sent_datetime=datetime.now(),
                    )
            foia.date_estimate = form.cleaned_data['date_estimate']
            foia.tracking_id = form.cleaned_data['tracking_id']
            foia.status = form.cleaned_data['status']
            if foia.status == 'payment':
                foia.price = form.cleaned_data['price']
            foia.save()
            foia.process_attachments(request.user)
            if foia.agency:
                foia.agency.unmark_stale()
            comm.create_agency_notifications()
            FlaggedTask.objects.create(
                    user=self.request.user,
                    foia=foia,
                    text='An agency used its login to update this request',
                    )
            messages.success(request, 'Reply succesfully posted')
        else:
            self.agency_reply_form = form
            raise FormError

        return redirect(foia.get_absolute_url() + '#')


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
    return render(
            request,
            'staff/acronyms.html',
            {'codes': codes},
            )
