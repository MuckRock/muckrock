"""
Views for the Task application
"""

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic.list import ListView
from django.shortcuts import redirect
from django.utils.datastructures import MultiValueDictKeyError

from muckrock.task.models import Task, OrphanTask, SnailMailTask, RejectedEmailTask, \
                                 StaleAgencyTask, FlaggedTask, NewAgencyTask, ResponseTask


class List(ListView):
    """List of tasks"""
    paginate_by = 25
    queryset = Task.objects.filter(resolved=False)
    context_object_name = 'tasks'

    @method_decorator(user_passes_test(lambda u: u.is_staff))
    def dispatch(self, *args, **kwargs):
        """Dispatch overriden to limit access"""
        return super(List, self).dispatch(*args, **kwargs)

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
