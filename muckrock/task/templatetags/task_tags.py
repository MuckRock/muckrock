from django import template

from muckrock.task.models import Task

import logging

register = template.Library()

class TaskNode(template.Node):
    """A base class for rendering a task into a template."""
    model = Task
    task_template = 'task/default.html'

    def __init__(self, task_id):
        """The node should be initialized with a task object"""
        self.task_id = template.Variable(task_id)

    def render(self, context):
        """Render the task"""
        try:
            task = self.model.objects.get(id=self.task_id.resolve(context))
        except (template.VariableDoesNotExist, self.model.DoesNotExist):
            return ''
        context.update(self.get_extra_context(task))
        return template.loader.render_to_string(
            self.task_template,
            context
        )

    def get_extra_context(self, task):
        """Returns a dictionary of context for the specific task"""
        extra_context = {'task': task}
        return extra_context

@register.tag
def task(parser, token):
    """Returns the correct task node given a task ID"""
    try:
        tag_name, task_id = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%s tag requires a single argument." % token.contents.split()[0])
    return TaskNode(task_id)
