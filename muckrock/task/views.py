"""
Views for the Task application
"""

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.decorators import method_decorator
from django.views.generic.list import ListView

from muckrock.task.models import Task, OrphanTask, SnailMailTask, RejectedEmailTask, \
                                 StaleAgencyTask, FlaggedTask, NewAgencyTask, ResponseTask
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
