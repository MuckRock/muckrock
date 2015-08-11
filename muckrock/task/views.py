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

    def post(self, request):
        """Handle general cases for updating Task objects"""
        # pylint: disable=no-self-use

        # every request should specify the task or tasks it is updating
        task_pk = request.POST.get('task')
        tasks_pks = request.POST.getlist('tasks')
        if task_pk or tasks_pks:
            if task_pk:
                tasks = [get_object_or_404(Task, pk=task_pk)]
            else:
                tasks = [get_object_or_404(Task, pk=each_pk) for each_pk in tasks_pks]
        else:
            messages.warning(request, 'No tasks were selected, so there\'s nothing to do!')
            return redirect('task-list')

        # These actions are shared between all Task objects
        for task in tasks:
            if request.POST.get('resolve') and not hasattr(task, 'responsetask'):
                # dont resolve response tasks here, do it in
                # the handler below after checking for errors
                task.resolve(request.user)

        orphan_task_post_handler(request, task_pk)
        snail_mail_task_post_handler(request, task_pk)
        new_agency_task_post_handler(request, task_pk)
        response_task_post_handler(request, task_pk)

        match = resolve(request.path)
        return redirect(match.url_name)

def orphan_task_post_handler(request, task_pk):
    """Special post handlers exclusive to OrphanTasks"""
    try:
        orphan_task = OrphanTask.objects.get(pk=task_pk)
    except OrphanTask.DoesNotExist:
        return

    if request.POST.get('reject'):
        orphan_task.reject()
        orphan_task.resolve(request.user)
    elif request.POST.get('move'):
        foia_pks = request.POST.get('move', '')
        foia_pks = foia_pks.split(', ')
        try:
            orphan_task.move(foia_pks)
            orphan_task.resolve(request.user)
            messages.success(request, 'The communication was moved to the specified requests.')
        except ValueError:
            messages.error(request, 'No valid requests to move communication to.')
    return

def snail_mail_task_post_handler(request, task_pk):
    """Special post handlers exclusive to SnailMailTasks"""
    try:
        snail_mail_task = SnailMailTask.objects.get(pk=task_pk)
    except SnailMailTask.DoesNotExist:
        return
    if request.POST.get('status'):
        status = request.POST.get('status')
        if status in dict(STATUS):
            snail_mail_task.set_status(status)
    if request.POST.get('update_date'):
        snail_mail_task.update_date()
    return

def new_agency_task_post_handler(request, task_pk):
    """Special post handlers exclusive to NewAgencyTasks"""
    try:
        new_agency_task = NewAgencyTask.objects.get(pk=task_pk)
    except NewAgencyTask.DoesNotExist:
        return
    if request.POST.get('approve'):
        new_agency_form = AgencyForm(request.POST, instance=new_agency_task.agency)
        if new_agency_form.is_valid():
            new_agency_form.save()
        else:
            messages.error(request, 'The agency info form was invalid. Sorry!')
            return
        new_agency_task.approve()
        new_agency_task.resolve(request.user)
    if request.POST.get('reject'):
        replacement_agency_id = request.POST.get('replacement')
        replacement_agency = get_object_or_404(Agency, id=replacement_agency_id)
        new_agency_task.reject(replacement_agency)
        new_agency_task.resolve(request.user)
    return

def response_task_post_handler(request, task_pk):
    """Special post handlers exclusive to ResponseTask"""
    try:
        response_task = ResponseTask.objects.get(pk=task_pk)
    except ResponseTask.DoesNotExist:
        return
    error_happened = False
    form = ResponseTaskForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Form is invalid')
        return
    cleaned_data = form.cleaned_data
    status = cleaned_data['status']
    move = cleaned_data['move']
    tracking_number = cleaned_data['tracking_number']
    # make sure that the move is executed first, so that the status
    # and tracking operations are applied to the correct FOIA request
    if move:
        try:
            response_task.move(move)
        except (Http404, ValueError):
            messages.error(request, 'No valid destination for moving the request.')
            error_happened = True
    if status:
        try:
            response_task.set_status(status)
        except ValueError:
            messages.error(request, 'You tried to set an invalid status. How did you manage that?')
            error_happened = True
    if tracking_number:
        try:
            response_task.set_tracking_id(tracking_number)
        except ValueError:
            messages.error(request,
                'You tried to set an invalid tracking id. Just use a string of characters.')
            error_happened = True
    if (move or status or tracking_number) and not error_happened:
        response_task.resolve(request.user)
    return

class OrphanTaskList(TaskList):
    title = 'Orphans'
    model = OrphanTask
    bulk_actions = ['reject']

class SnailMailTaskList(TaskList):
    title = 'Snail Mails'
    model = SnailMailTask

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

class ResponseTaskList(TaskList):
    title = 'Responses'
    model = ResponseTask

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
