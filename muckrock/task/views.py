"""
Views for the Task application
"""
from django import template
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.core.urlresolvers import resolve
from django.shortcuts import redirect, get_object_or_404
from django.utils.decorators import method_decorator

import logging

from muckrock.foia.models import STATUS
from muckrock.task.forms import TaskFilterForm, NewAgencyForm
from muckrock.task.models import Task, OrphanTask, SnailMailTask, RejectedEmailTask, \
                                 StaleAgencyTask, FlaggedTask, NewAgencyTask, ResponseTask
from muckrock.views import MRFilterableListView

# pylint:disable=missing-docstring

def render_list(tasks):
    """Renders a task widget for each task in the list"""
    rendered_tasks = []
    for task in tasks:
        
        # set up a baseline data to render and template to use
        
        task_context = {'task': task}
        task_template = 'task/default.html'
        
        # customize task template and data here
        
        try:
            task = OrphanTask.objects.get(id=task.id)
            logging.debug('Is orphan task.')
            task_context.update({'status': STATUS})
            task_template = 'task/orphantask.html'
        except OrphanTask.DoesNotExist:
            logging.debug('Is not orphan task.')
            pass
        
        try:
            task = SnailMailTask.objects.get(id=task.id)
            logging.debug('Is snail mail task.')
            task_template = 'task/snail_mail.html'
        except SnailMailTask.DoesNotExist:
            logging.debug('Is not snail mail task.')
            pass

        try:
            task = RejectedEmailTask.objects.get(id=task.id)
            task_template = 'task/rejected_email.html'
        except RejectedEmailTask.DoesNotExist:
            pass
    
        try:
            task = ResponseTask.objects.get(id=task.id)
            context = {'status': STATUS}
            task_context.update(context)
            task_template = 'task/rejected_email.html'
        except ResponseTask.DoesNotExist:
            pass

        # render and append
    
        task_template = template.loader.get_template(task_template)
        task_context = template.Context(task_context)
        rendered_tasks.append(task_template.render(task_context))
            
    return rendered_tasks

def count_tasks():
    """Counts all unresolved tasks and adds them to a dictionary"""
    count = {}
    count['all'] =          Task.objects.exclude(resolved=True).count()
    count['orphan'] =       OrphanTask.objects.exclude(resolved=True).count()
    count['snail_mail'] =   SnailMailTask.objects.exclude(resolved=True).count()
    count['rejected'] =     RejectedEmailTask.objects.exclude(resolved=True).count()
    count['stale_agency'] = StaleAgencyTask.objects.exclude(resolved=True).count()
    count['flagged'] =      FlaggedTask.objects.exclude(resolved=True).count()
    count['new_agency'] =   NewAgencyTask.objects.exclude(resolved=True).count()
    count['response'] =     ResponseTask.objects.exclude(resolved=True).count()
    return count

class TaskList(MRFilterableListView):
    """List of tasks"""
    title = 'Tasks'
    template_name = 'lists/task_list.html'
    model = Task

    def get_queryset(self):
        """Remove resolved tasks unless filter says to keep them"""
        queryset = super(TaskList, self).get_queryset()

        if not self.request.GET.get('show_resolved'):
            queryset = queryset.exclude(resolved=True)
        return queryset

    def get_context_data(self, **kwargs):
        """Adds counters for each of the sections (except all) and uses TaskFilterForm"""
        context = super(TaskList, self).get_context_data(**kwargs)
        if self.request.GET.get('show_resolved'):
            context['filter_form'] = TaskFilterForm(initial={'show_resolved': True})
        else:
            context['filter_form'] = TaskFilterForm()
        context['counters'] = count_tasks()
        context['object_list'] = render_list(context['object_list'])
        return context

    @method_decorator(user_passes_test(lambda u: u.is_staff))
    def dispatch(self, *args, **kwargs):
        """Dispatch overriden to limit access"""
        return super(TaskList, self).dispatch(*args, **kwargs)

    def post(self, request):
        """Handle general cases for updating Task objects"""
        # pylint: disable=no-self-use
        # every request should specify the task it is updating
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

        for task in tasks:
            # These actions are shared between all Task objects
            # resolve will either be True or None
            # the task will only resolve if True
            if request.POST.get('resolve'):
                task.resolve(request.user)
            if request.POST.get('assign'):
                user_pk = request.POST.get('assign')
                user = get_object_or_404(User, pk=user_pk)
                task.assign(user)

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
    elif request.POST.get('move'):
        foia_pks = request.POST.get('move', '')
        foia_pks = foia_pks.split(', ')
        orphan_task.move(request, foia_pks)

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
    return

def new_agency_task_post_handler(request, task_pk):
    """Special post handlers exclusive to NewAgencyTasks"""
    try:
        new_agency_task = NewAgencyTask.objects.get(pk=task_pk)
    except NewAgencyTask.DoesNotExist:
        return
    if request.POST.get('approve'):
        new_agency_task.approve()
    if request.POST.get('reject'):
        new_agency_task.reject()
    return

def response_task_post_handler(request, task_pk):
    """Special post handlers exclusive to ResponseTask"""
    try:
        response_task = ResponseTask.objects.get(pk=task_pk)
    except ResponseTask.DoesNotExist:
        return
    if request.POST.get('status'):
        status = request.POST.get('status')
        if status in dict(STATUS):
            response_task.set_status(status)
    return

class OrphanTaskList(TaskList):
    title = 'Orphans'
    model = OrphanTask

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
