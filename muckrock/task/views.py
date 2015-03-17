"""
Views for the Task application
"""

from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.utils.decorators import method_decorator

from muckrock.task.models import Task
from muckrock.views import MRFilterableListView

class TaskList(MRFilterableListView):
    """List of tasks"""
    title = 'Tasks'
    template_name = 'lists/task_list.html'
    model = Task

    @method_decorator(user_passes_test(lambda u: u.is_staff))
    def dispatch(self, *args, **kwargs):
        """Dispatch overriden to limit access"""
        return super(TaskList, self).dispatch(*args, **kwargs)

    def post(self, request):
        """Handle general cases for updating Task objects"""
        # every request should specify the task it is updating
        task_pk = request.POST.get('task')
        task = get_object_or_404(Task, pk=task_pk)
        # resolve will either be True or None
        # the task will only resolve if True
        if request.POST.get('resolve'):
            task.resolve()
        if request.POST.get('assign'):
            user_pk = request.POST.get('assign')
            user = get_object_or_404(User, pk=user_pk)
            task.assign(user)
        return redirect('task-list')

@user_passes_test(lambda u: u.is_staff)
def assign(request):
    """Assign a user to a task, AJAX style"""
    user_pk = request.POST.get('user')
    task_pk = request.POST.get('task')
    try:
        if user_pk == '0':
            user = None
        else:
            user = User.objects.get(pk=user_pk)
        task = Task.objects.get(pk=task_pk)
    except (User.DoesNotExist, Task.DoesNotExist):
        return HttpResponse("Error", content_type='text/plain')

    task.assigned = user
    task.save()
    return HttpResponse("OK", content_type='text/plain')
