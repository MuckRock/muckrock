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
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.list import ListView

from muckrock.task.models import Task, OrphanTask, SnailMailTask, RejectedEmailTask, \
                                 StaleAgencyTask, FlaggedTask, NewAgencyTask, ResponseTask


class List(ListView):
    """List of tasks"""
    paginate_by = 25
    context_object_name = 'tasks'

    @method_decorator(user_passes_test(lambda u: u.is_staff))
    def dispatch(self, *args, **kwargs):
        """Dispatch overriden to limit access"""
        return super(List, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        """Filter by user"""
        username = self.request.GET.get('user')
        tasks = Task.objects.filter(resolved=False)
        if username:
            try:
                user = User.objects.get(username=username)
                tasks = tasks.filter(assigned=user)
            except User.DoesNotExist:
                pass
        return tasks

    def post(self, request):
        """Handle form submissions"""
        # pylint: disable=no-self-use
        task_classes = {
                'flaggedtask': FlaggedTask,
                'snailmailtask': SnailMailTask,
                'newagencytask': NewAgencyTask,
                'staleagencytask': StaleAgencyTask,
                'orphantask': OrphanTask,
                'responsetask': ResponseTask,
                'rejectedemailtask': RejectedEmailTask,
                }
        try:
            task = task_classes[request.POST['task_class']].objects.\
                    get(pk=request.POST['task_pk'])
        except (Task.DoesNotExist, KeyError, MultiValueDictKeyError):
            messages.error(request, 'Error finding that task')

        task.handle_post(request)

        return redirect('task-list')

    def get_context_data(self, **kwargs):
        context = super(List, self).get_context_data(**kwargs)
        context['staff_users'] = User.objects.filter(is_staff=True)
        return context


# XXX set the csrf on the ajax request instead of doing this
@csrf_exempt
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
    except User.DoesNotExist, Task.DoesNotExist:
        return HttpResponse("Error", content_type='text/plain')

    task.assigned = user
    task.save()
    return HttpResponse("OK", content_type='text/plain')
