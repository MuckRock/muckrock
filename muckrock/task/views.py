"""
Views for the Task application
"""

from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic.list import ListView

from muckrock.task.models import Task


class List(ListView):
    """List of news articles"""
    paginate_by = 25
    model = Task
    context_object_name = 'tasks'

    @method_decorator(user_passes_test(lambda u: u.is_staff))
    def dispatch(self, *args, **kwargs):
        """Dispatch overriden to limit access"""
        return super(List, self).dispatch(*args, **kwargs)
