"""
Views for the Task application
"""

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import resolve
from django.db.models import Count, Prefetch, Q, Max
from django.http import HttpResponse, Http404
from django.shortcuts import redirect, get_object_or_404
from django.utils.decorators import method_decorator

import logging

from muckrock.agency.forms import AgencyForm
from muckrock.agency.models import Agency, STALE_DURATION
from muckrock.foia.models import STATUS, FOIARequest, FOIACommunication, FOIAFile
from muckrock.models import ExtractDay, Now
from muckrock.task.forms import (
    TaskFilterForm, FlaggedTaskForm, StaleAgencyTaskForm, ResponseTaskForm,
    ProjectReviewTaskForm
    )
from muckrock.task.models import (
    Task, OrphanTask, SnailMailTask, RejectedEmailTask,
    StaleAgencyTask, FlaggedTask, NewAgencyTask, ResponseTask,
    CrowdfundTask, MultiRequestTask, StatusChangeTask, FailedFaxTask,
    ProjectReviewTask
    )
from muckrock.views import MRFilterableListView

# pylint:disable=missing-docstring

def count_tasks():
    """Counts all unresolved tasks and adds them to a dictionary"""
    count = Task.objects.filter(resolved=False).aggregate(
        all=Count('id'),
        orphan=Count('orphantask'),
        snail_mail=Count('snailmailtask'),
        rejected=Count('rejectedemailtask'),
        stale_agency=Count('staleagencytask'),
        flagged=Count('flaggedtask'),
        projectreview=Count('projectreviewtask'),
        new_agency=Count('newagencytask'),
        response=Count('responsetask'),
        status_change=Count('statuschangetask'),
        crowdfund=Count('crowdfundtask'),
        multirequest=Count('multirequesttask'),
        failed_fax=Count('failedfaxtask'),
        )
    return count


class TaskList(MRFilterableListView):
    """List of tasks"""
    title = 'Tasks'
    model = Task
    template_name = 'lists/task_list.html'
    default_sort = 'pk'
    bulk_actions = ['resolve'] # bulk actions have to be lowercase and 1 word

    def get_queryset(self):
        """Apply query parameters to the queryset"""
        queryset = super(TaskList, self).get_queryset()
        task_pk = self.kwargs.get('pk')
        show_resolved = self.request.GET.get('show_resolved')
        resolved_by = self.request.GET.get('resolved_by')
        if task_pk:
            # when we are looking for a specific task,
            # we filter the queryset for that task's pk
            # and override show_resolved and resolved_by
            queryset = queryset.filter(pk=task_pk)
            if queryset.count() == 0:
                raise Http404()
            show_resolved = True
            resolved_by = None
        if not show_resolved:
            queryset = queryset.exclude(resolved=True)
        if resolved_by:
            queryset = queryset.filter(resolved_by__pk=resolved_by)
        # order queryset
        queryset = queryset.order_by('date_done', 'date_created')
        return queryset

    def get_context_data(self, **kwargs):
        """Adds counters for each of the sections (except all) and uses TaskFilterForm"""
        context = super(TaskList, self).get_context_data(**kwargs)
        filter_initial = {}
        show_resolved = self.request.GET.get('show_resolved')
        if show_resolved:
            filter_initial['show_resolved'] = True
        resolved_by = self.request.GET.get('resolved_by')
        if resolved_by:
            filter_initial['resolved_by'] = resolved_by
        context['filter_form'] = TaskFilterForm(initial=filter_initial)
        context['counters'] = count_tasks()
        context['bulk_actions'] = self.bulk_actions
        return context

    @method_decorator(user_passes_test(lambda u: u.is_staff))
    def dispatch(self, *args, **kwargs):
        """Dispatch overriden to limit access"""
        return super(TaskList, self).dispatch(*args, **kwargs)

    def get_redirect_url(self):
        """Returns the url to redirect to"""
        resolved_url = resolve(self.request.path)
        return resolved_url.url_name

    def get_tasks(self):
        """Every request should specify the task or tasks it is updating as PKs"""
        post_data = self.request.POST
        task_pks = [post_data.get('task')] + post_data.getlist('tasks')
        # clean the list of task_pks
        task_pks = [int(task_pk) for task_pk in task_pks if task_pk is not None]
        if not task_pks:
            raise ValueError('No tasks were selected, so there\'s nothing to do!')
        tasks = [get_object_or_404(self.get_model(), pk=each_pk) for each_pk in task_pks]
        return tasks

    def task_post_helper(self, request, task):
        """Specific actions to apply to the task"""
        # pylint: disable=no-self-use
        if request.POST.get('resolve'):
            task.resolve(request.user)
        return

    def post(self, request):
        """Handle general cases for updating Task objects"""
        try:
            tasks = self.get_tasks()
        except ValueError as exception:
            if request.is_ajax():
                return HttpResponse(400)
            else:
                messages.warning(self.request, exception)
                return redirect(self.get_redirect_url())
        for task in tasks:
            self.task_post_helper(request, task)
        if request.is_ajax():
            return HttpResponse(200)
        else:
            return redirect(self.get_redirect_url())


class OrphanTaskList(TaskList):
    model = OrphanTask
    title = 'Orphans'
    queryset = (OrphanTask.objects
            .select_related('communication__likely_foia__jurisdiction')
            .prefetch_related('communication__files'))
    bulk_actions = ['reject']

    def task_post_helper(self, request, task):
        """Special post helper exclusive to OrphanTasks"""
        if request.POST.get('reject'):
            blacklist = request.POST.get('blacklist', False)
            task.reject(blacklist)
            task.resolve(request.user)
        elif request.POST.get('move'):
            foia_pks = request.POST.get('move', '')
            foia_pks = foia_pks.split(', ')
            try:
                task.move(foia_pks)
                task.resolve(request.user)
                messages.success(request, 'The communication was moved to the specified requests.')
            except ValueError as exception:
                messages.error(request, 'Error when moving: %s', exception)
                logging.debug('Error moving communications: %s', exception)
            except Http404:
                messages.error(request, 'Tried to move to a nonexistant request.')
                logging.debug('Tried to move to a nonexistant request.')
        return


class SnailMailTaskList(TaskList):
    model = SnailMailTask
    title = 'Snail Mails'
    queryset = (SnailMailTask.objects
            .select_related(
                'communication__foia__agency',
                'communication__foia__user',
                'communication__foia__jurisdiction',
                )
            .prefetch_related(
                Prefetch(
                    'communication__foia__communications',
                    queryset=FOIACommunication.objects.filter(response=True),
                    to_attr='has_ack'),
                Prefetch(
                    'communication__foia__communications',
                    queryset=FOIACommunication.objects.order_by('-date'),
                    to_attr='reverse_communications'),
                )
            )

    def task_post_helper(self, request, task):
        """Special post helper exclusive to SnailMailTasks"""
        # we should always set the status of a request when resolving
        # a snail mail task so that the request leaves processing status
        if request.POST.get('status'):
            status = request.POST.get('status')
            if status in dict(STATUS):
                task.set_status(status)
            # updating the date is an option and not an action
            if request.POST.get('update_date'):
                task.update_date()
        # if the task is in the payment category and we're given a check
        # number, then we should record the existence of this check
        if request.POST.get('check_number') and task.category == 'p':
            check_number = int(request.POST.get('check_number'))
            task.record_check(check_number, request.user)
        task.resolve(request.user)
        return


class RejectedEmailTaskList(TaskList):
    model = RejectedEmailTask
    title = 'Rejected Emails'
    queryset = RejectedEmailTask.objects.select_related('foia__jurisdiction')

    def get_context_data(self, **kwargs):
        """Prefetch the agencies and foias sharing an email"""
        context = super(RejectedEmailTaskList, self).get_context_data(**kwargs)
        email_filter = Q()
        all_emails = {t.email for t in context['object_list']}
        for email in all_emails:
            email_filter |= Q(email__iexact=email)
            email_filter |= Q(other_emails__icontains=email)
        agencies = Agency.objects.filter(email_filter)
        statuses = ('ack', 'processed', 'appealing', 'fix', 'payment')
        foias = (FOIARequest.objects.filter(email_filter)
                .filter(status__in=statuses)
                .select_related('jurisdiction')
                .order_by())
        def seperate_by_email(objects, emails):
            """Make a dictionary of each email to the objects having that email"""
            return_value = {}
            for email in emails:
                email_upper = email.upper()
                return_value[email] = [o for o in objects if
                        email_upper == o.email.upper() or
                        email_upper in o.other_emails.upper()]
            return return_value
        agency_by_email = seperate_by_email(agencies, all_emails)
        foia_by_email = seperate_by_email(foias, all_emails)
        for task in context['object_list']:
            task.foias = foia_by_email[task.email]
            task.agencies = agency_by_email[task.email]
        return context


class StaleAgencyTaskList(TaskList):
    model = StaleAgencyTask
    title = 'Stale Agencies'
    queryset = (StaleAgencyTask.objects
            .select_related('agency')
            .prefetch_related(
                'agency__foiarequest_set__communications__foia__jurisdiction',
                Prefetch('agency__foiarequest_set',
                    queryset=FOIARequest.objects
                    .get_open()
                    .select_related('jurisdiction')
                    .filter(communications__response=True)
                    .annotate(latest_response=ExtractDay(
                        Now() - Max('communications__date')))
                    .filter(latest_response__gte=STALE_DURATION)
                    .order_by('-latest_response'),
                    to_attr='stale_requests_'),
                ))

    def task_post_helper(self, request, task):
        """Check the new email is valid and, if so, apply it"""
        if request.POST.get('update'):
            email_form = StaleAgencyTaskForm(request.POST)
            if email_form.is_valid():
                new_email = email_form.cleaned_data['email']
                foia_pks = request.POST.getlist('foia')
                foias = FOIARequest.objects.filter(pk__in=foia_pks)
                task.update_email(new_email, foias)
            else:
                messages.error(request, 'The email is invalid.')
                return
        if request.POST.get('resolve'):
            task.resolve(request.user)


class FlaggedTaskList(TaskList):
    model = FlaggedTask
    title = 'Flagged'
    queryset = FlaggedTask.objects.select_related(
            'user', 'foia__jurisdiction', 'agency', 'jurisdiction')

    def task_post_helper(self, request, task):
        """Special post handler for FlaggedTasks"""
        if request.POST.get('reply'):
            reply_form = FlaggedTaskForm(request.POST)
            if reply_form.is_valid() and task.user:
                text = reply_form.cleaned_data['text']
                task.reply(text)
            elif reply_form.is_valid():
                messages.error(request, 'Cannot reply - task has no user')
                return
            else:
                messages.error(request, 'The form is invalid')
                return
        if request.POST.get('resolve'):
            task.resolve(request.user)


class ProjectReviewTaskList(TaskList):
    model = ProjectReviewTask
    title = 'Pending Projects'
    queryset = (ProjectReviewTask.objects.select_related('project')
                                        .prefetch_related('project__requests')
                                        .prefetch_related('project__articles')
                                        .prefetch_related('project__contributors'))

    def task_post_helper(self, request, task):
        """Special post handler for ProjectReviewTasks"""
        form = ProjectReviewTaskForm(request.POST)
        if form.is_valid():
            text = form.cleaned_data['reply']
            action = request.POST.get('action', None)
            if action == 'reply':
                task.reply(text)
            elif action == 'approve':
                task.approve(text)
                task.resolve(request.user)
            elif action == 'reject':
                task.reject(text)
                task.resolve(request.user)


class NewAgencyTaskList(TaskList):
    title = 'New Agencies'
    queryset = NewAgencyTask.objects.preload_list()

    def task_post_helper(self, request, task):
        """Special post handlers exclusive to NewAgencyTasks"""
        if request.POST.get('approve'):
            new_agency_form = AgencyForm(request.POST, instance=task.agency)
            if new_agency_form.is_valid():
                new_agency_form.save()
            else:
                messages.error(request, 'The agency info form is invalid.')
                return
            task.approve()
            task.resolve(request.user)
        if request.POST.get('reject'):
            replacement_agency_id = request.POST.get('replacement')
            replacement_agency = get_object_or_404(Agency, id=replacement_agency_id)
            task.reject(replacement_agency)
            task.resolve(request.user)
        return


class ResponseTaskList(TaskList):
    title = 'Responses'
    queryset = (ResponseTask.objects
            .select_related('communication__foia__agency')
            .select_related('communication__foia__jurisdiction')
            .prefetch_related(
                Prefetch('communication__files',
                    queryset=FOIAFile.objects.select_related('foia__jurisdiction')),
                Prefetch('communication__foia__communications',
                    queryset=FOIACommunication.objects
                        .order_by('-date')
                        .prefetch_related('files'),
                    to_attr='reverse_communications'),
                ))

    def task_post_helper(self, request, task):
        """Special post helper exclusive to ResponseTask"""
        # pylint: disable=too-many-branches
        error_happened = False
        form = ResponseTaskForm(request.POST)
        if not form.is_valid():
            messages.error(request, 'Form is invalid')
            return
        cleaned_data = form.cleaned_data
        status = cleaned_data['status']
        set_foia = cleaned_data['set_foia']
        move = cleaned_data['move']
        tracking_number = cleaned_data['tracking_number']
        date_estimate = cleaned_data['date_estimate']
        price = cleaned_data['price']
        proxy = cleaned_data['proxy']
        # move is executed first, so that the status and tracking
        # operations are applied to the correct FOIA request
        if move:
            try:
                task.move(move)
            except (Http404, ValueError):
                messages.error(request, 'No valid destination for moving the request.')
                error_happened = True
        if status:
            try:
                task.set_status(status, set_foia)
            except ValueError:
                messages.error(request, 'You tried to set the request to an invalid status.')
                error_happened = True
        if tracking_number:
            try:
                task.set_tracking_id(tracking_number)
            except ValueError:
                messages.error(request,
                    'You tried to set an invalid tracking id. Just use a string of characters.')
                error_happened = True
        if date_estimate:
            try:
                task.set_date_estimate(date_estimate)
            except ValueError:
                messages.error(request, 'You tried to set the request to an invalid date.')
                error_happened = True
        if price:
            try:
                task.set_price(price)
            except ValueError:
                messages.error(request, 'You tried to set a non-numeric price.')
                error_happened = True
        if proxy:
            task.proxy_reject()
        action_taken = move or status or tracking_number or price or proxy
        if action_taken and not error_happened:
            task.resolve(request.user)


class StatusChangeTaskList(TaskList):
    title = 'Status Change'
    queryset = StatusChangeTask.objects.select_related(
            'user', 'foia__jurisdiction')


class CrowdfundTaskList(TaskList):
    title = 'Crowdfunds'
    queryset = CrowdfundTask.objects.select_related('crowdfund')


class MultiRequestTaskList(TaskList):
    title = 'Multi-Requests'
    queryset = (MultiRequestTask.objects
            .select_related('multirequest__user')
            .prefetch_related('multirequest__agencies'))


class FailedFaxTaskList(TaskList):
    title = 'Failed Faxes'
    queryset = (FailedFaxTask.objects
            .select_related('communication__foia__agency')
            .select_related('communication__foia__user')
            .select_related('communication__foia__jurisdiction')
            .prefetch_related(
                Prefetch(
                    'communication__foia__communications',
                    queryset=FOIACommunication.objects.order_by('-date'),
                    to_attr='reverse_communications')))


class RequestTaskList(TaskList):
    """Displays all the tasks for a given request."""
    title = 'Request Tasks'
    template_name = 'lists/request_task_list.html'

    def get_queryset(self):
        # pylint: disable=attribute-defined-outside-init
        # pylint: disable=unsubscriptable-object
        self.foia_request = get_object_or_404(
                FOIARequest.objects.select_related(
                    'agency__jurisdiction',
                    'jurisdiction__parent__parent',
                    'user__profile'),
                pk=self.kwargs['pk'])
        user = self.request.user
        tasks = Task.objects.filter_by_foia(self.foia_request, user)
        return tasks

    def get_context_data(self, **kwargs):
        # pylint: disable=bad-super-call
        # we purposely call super on TaskList here, as we do want the generic
        # list views method to be called, but we don't need any of the
        # data calculated in the TaskList method, so using it just slows us down
        context = super(TaskList, self).get_context_data(**kwargs)
        context['foia'] = self.foia_request
        context['foia_url'] = self.foia_request.get_absolute_url()
        return context
