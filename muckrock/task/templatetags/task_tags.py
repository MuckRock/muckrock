from django import template

from muckrock.task.models import Task

register = template.Library()

class TaskNode(template.Node):
    """A base class for rendering a task into a template."""
    model = Task
    task_template = 'task/default.html'

    def __init__(self, task_id):
        """The node should be initialized with a task object"""
        self.task = self.model.objects.get(id=task_id)

    def render(self, context):
        """Render the table headers"""
        context.update(self.get_extra_context())
        return template.loader.render_to_string(
            task_template,
            context,
            context_instance=template.RequestContext(self.request)
        )

    def get_extra_context(self):
        """Returns a dictionary of context for the specific task"""
        extra_context = {'task': self.task}
        return extra_context

@register.tag
def task(parser, token):
    """Returns the correct task node given a task ID"""
    try:
        task_id = token[1:]
        return TaskNode(task_id)
    except IndexError:
        logging.error('No argument provided to task tag.')
    except Task.DoesNotExist:
        logging.error('The task does not exist.')
    return None
