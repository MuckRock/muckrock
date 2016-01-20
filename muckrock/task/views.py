"""
Views for the Task application
"""

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import resolve
from django.db.models import Count, Prefetch
from django.http import HttpResponse, Http404
from django.shortcuts import redirect, get_object_or_404
from django.utils.decorators import method_decorator

import logging

from muckrock.agency.forms import AgencyForm
from muckrock.agency.models import Agency
from muckrock.foia.models import STATUS, FOIARequest, FOIACommunication, FOIAFile
from muckrock.task.forms import TaskFilterForm, ResponseTaskForm
from muckrock.task.models import Task, OrphanTask, SnailMailTask, RejectedEmailTask, \
                                 StaleAgencyTask, FlaggedTask, NewAgencyTask, ResponseTask, \
                                 PaymentTask, GenericCrowdfundTask, MultiRequestTask, \
                                 StatusChangeTask, FailedFaxTask
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
            new_agency=Count('newagencytask'),
            response=Count('responsetask'),
            status_change=Count('statuschangetask'),
            payment=Count('paymenttask'),
            crowdfund=Count('genericcrowdfundtask'),
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
        filter_ids = self.request.GET.getlist('id')
        show_resolved = self.request.GET.get('show_resolved')
        resolved_by = self.request.GET.get('resolved_by')
        # first we have to check the integrity of the id values
        for filter_id in filter_ids:
            try:
                filter_id = int(filter_id)
            except ValueError:
                filter_ids.remove(filter_id)
        if filter_ids:
            queryset = queryset.filter(id__in=filter_ids)
            show_resolved = True
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
        context['type'] = self.get_model().__name__
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
    title = 'Orphans'
    queryset = (OrphanTask.objects
            .select_related('communication__likely_foia')
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
    title = 'Snail Mails'
    queryset = (SnailMailTask.objects
            .select_related(
                'communication__foia__agency',
                'communication__foia__user',
                )
            .prefetch_related(
                Prefetch(
                    'communication__foia__communications',
                    queryset=FOIACommunication.objects.order_by('-date'),
                    to_attr='reverse_communications'),
                Prefetch(
                    'communication__foia__communications',
                    queryset=FOIACommunication.objects.filter(response=True),
                    to_attr='has_ack'),
                ))

    def task_post_helper(self, request, task):
        """Special post helper exclusive to SnailMailTasks"""
        if request.POST.get('status'):
            status = request.POST.get('status')
            if status in dict(STATUS):
                task.set_status(status)
                task.resolve(request.user)
            # updating the date is an option and not an action
            if request.POST.get('update_date'):
                task.update_date()
        return


class RejectedEmailTaskList(TaskList):
    title = 'Rejected Emails'
    # XXX how to prefetch foias and agencies sharing an email??
    queryset = RejectedEmailTask.objects.select_related('foia')


class StaleAgencyTaskList(TaskList):
    title = 'Stale Agencies'
    queryset = StaleAgencyTask.objects.select_related('agency')


class FlaggedTaskList(TaskList):
    title = 'Flagged'
    queryset = FlaggedTask.objects.select_related(
            'user', 'foia', 'agency', 'jurisdiction')


class NewAgencyTaskList(TaskList):
    title = 'New Agencies'
    queryset = (NewAgencyTask.objects
            .select_related('agency__jurisdiction')
            .prefetch_related(
                Prefetch('agency__foiarequest_set',
                    queryset=FOIARequest.objects.select_related('jurisdiction')),
                Prefetch('agency__jurisdiction__agencies',
                    queryset=Agency.objects
                    .filter(status='approved')
                    .order_by('name'),
                    to_attr='other_agencies')))

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
            .select_related('communication__foia')
            .prefetch_related(
                Prefetch('communication__files',
                    queryset=FOIAFile.objects.select_related('foia__jurisdiction')),
                Prefetch('communication__foia__communications',
                    queryset=FOIACommunication.objects.order_by('-date'),
                    to_attr='reverse_communications'),
                ))

    def task_post_helper(self, request, task):
        """Special post helper exclusive to ResponseTask"""
        error_happened = False
        form = ResponseTaskForm(request.POST)
        if not form.is_valid():
            messages.error(request, 'Form is invalid')
            return
        cleaned_data = form.cleaned_data
        status = cleaned_data['status']
        move = cleaned_data['move']
        tracking_number = cleaned_data['tracking_number']
        date_estimate = cleaned_data['date_estimate']
        price = cleaned_data['price']
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
                task.set_status(status)
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
        if (move or status or tracking_number or price) and not error_happened:
            task.resolve(request.user)
        return


class StatusChangeTaskList(TaskList):
    title = 'Status Change'
    queryset = StatusChangeTask.objects.select_related('user', 'foia')


class PaymentTaskList(TaskList):
    title = 'Payments'
    queryset = PaymentTask.objects.select_related('user', 'foia')


class CrowdfundTaskList(TaskList):
    title = 'Crowdfunds'
    # XXX generic FKs are problematic (can't select related on foia/project)
    queryset = GenericCrowdfundTask.objects.prefetch_related('crowdfund')


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
        foia_request = get_object_or_404(FOIARequest, pk=self.kwargs['pk'])
        tasks = Task.objects.filter_by_foia(foia_request)
        return tasks

    def get_context_data(self, **kwargs):
        context = super(RequestTaskList, self).get_context_data(**kwargs)
        context['foia'] = get_object_or_404(FOIARequest, pk=self.kwargs['pk'])
        return context
