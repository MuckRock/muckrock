"""
Views for the Task application
"""

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.core.urlresolvers import resolve
from django.http import Http404
from django.shortcuts import redirect, get_object_or_404
from django.utils.decorators import method_decorator

from muckrock.agency.forms import AgencyForm
from muckrock.agency.models import Agency
from muckrock import foia
from muckrock.task.forms import TaskFilterForm, ResponseTaskForm
from muckrock.task.models import Task, OrphanTask, SnailMailTask, RejectedEmailTask, \
                                 StaleAgencyTask, FlaggedTask, NewAgencyTask, ResponseTask, \
                                 PaymentTask, CrowdfundTask, MultiRequestTask, StatusChangeTask, \
                                 FailedFaxTask
from muckrock.views import MRFilterableListView

STATUS = foia.models.STATUS

# pylint:disable=missing-docstring

def count_tasks():
    """Counts all unresolved tasks and adds them to a dictionary"""
    count = {}
    count['all'] = Task.objects.exclude(resolved=True).count()
    count['orphan'] = OrphanTask.objects.exclude(resolved=True).count()
    count['snail_mail'] = SnailMailTask.objects.exclude(resolved=True).count()
    count['rejected'] = RejectedEmailTask.objects.exclude(resolved=True).count()
    count['stale_agency'] = StaleAgencyTask.objects.exclude(resolved=True).count()
    count['flagged'] = FlaggedTask.objects.exclude(resolved=True).count()
    count['new_agency'] = NewAgencyTask.objects.exclude(resolved=True).count()
    count['response'] = ResponseTask.objects.exclude(resolved=True).count()
    count['status_change'] = StatusChangeTask.objects.exclude(resolved=True).count()
    count['payment'] = PaymentTask.objects.exclude(resolved=True).count()
    count['crowdfund'] = CrowdfundTask.objects.exclude(resolved=True).count()
    count['multirequest'] = MultiRequestTask.objects.exclude(resolved=True).count()
    count['failed_fax'] = FailedFaxTask.objects.exclude(resolved=True).count()
    return count

class TaskList(MRFilterableListView):
    """List of tasks"""
    title = 'Tasks'
    model = Task
    template_name = 'lists/task_list.html'
    bulk_actions = ['resolve'] # bulk actions have to be lowercase and 1 word

    def get_queryset(self):
        """Apply query parameters to the queryset"""
        queryset = super(TaskList, self).get_queryset()
        filter_ids = self.request.GET.getlist('id')
        show_resolved = self.request.GET.get('show_resolved')
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
        # order queryset
        queryset = queryset.order_by('date_done', 'date_created')
        return queryset

    def get_context_data(self, **kwargs):
        """Adds counters for each of the sections (except all) and uses TaskFilterForm"""
        context = super(TaskList, self).get_context_data(**kwargs)
        if self.request.GET.get('show_resolved'):
            context['filter_form'] = TaskFilterForm(initial={'show_resolved': True})
        else:
            context['filter_form'] = TaskFilterForm()
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
        POST = self.request.POST
        task_pks = [POST.get('task')] + POST.getlist('tasks')
        # clean the list of task_pks
        task_pks = [int(task_pk) for task_pk in task_pks if task_pk is not None]
        if not task_pks:
            messages.warning(self.request, 'No tasks were selected, so there\'s nothing to do!')
            return redirect(self.get_redirect_url())
        tasks = [get_object_or_404(self.model, pk=each_pk) for each_pk in task_pks]
        return tasks

    def task_post_helper(self, request, task):
        """Specific actions to apply to the task"""
        if request.POST.get('resolve') and not hasattr(task, 'responsetask'):
            # dont resolve response tasks here, do it in
            # the handler below after checking for errors
            task.resolve(request.user)
        return

    def post(self, request):
        """Handle general cases for updating Task objects"""
        tasks = self.get_tasks()
        for task in tasks:
            self.task_post_helper(request, task)
        return redirect(self.get_redirect_url())


class OrphanTaskList(TaskList):
    title = 'Orphans'
    model = OrphanTask
    bulk_actions = ['reject']

    def task_post_helper(self, request, task):
        """Special post helper exclusive to OrphanTasks"""
        if request.POST.get('reject'):
            task.reject()
            task.resolve(request.user)
        elif request.POST.get('move'):
            foia_pks = request.POST.get('move', '')
            foia_pks = foia_pks.split(', ')
            try:
                task.move(foia_pks)
                task.resolve(request.user)
                messages.success(request, 'The communication was moved to the specified requests.')
            except ValueError:
                messages.error(request, 'No valid requests to move communication to.')
        return


class SnailMailTaskList(TaskList):
    title = 'Snail Mails'
    model = SnailMailTask

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
    model = RejectedEmailTask


class StaleAgencyTaskList(TaskList):
    title = 'Stale Agencies'
    model = StaleAgencyTask


class FlaggedTaskList(TaskList):
    title = 'Flagged'
    model = FlaggedTask


class NewAgencyTaskList(TaskList):
    title = 'New Agencies'
    model = NewAgencyTask

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
    model = ResponseTask

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
                messages.error(request, 'You tried to set an invalid status. How did you manage that?')
                error_happened = True
        if tracking_number:
            try:
                task.set_tracking_id(tracking_number)
            except ValueError:
                messages.error(request,
                    'You tried to set an invalid tracking id. Just use a string of characters.')
                error_happened = True
        if (move or status or tracking_number) and not error_happened:
            task.resolve(request.user)
        return


class StatusChangeTaskList(TaskList):
    title = 'Status Change'
    model = StatusChangeTask


class PaymentTaskList(TaskList):
    title = 'Payments'
    model = PaymentTask


class CrowdfundTaskList(TaskList):
    title = 'Crowdfunds'
    model = CrowdfundTask


class MultiRequestTaskList(TaskList):
    title = 'Multi-Requests'
    model = MultiRequestTask


class FailedFaxTaskList(TaskList):
    title = 'Failed Faxes'
    model = FailedFaxTask
