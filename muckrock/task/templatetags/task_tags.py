from django import template

from muckrock import task
from muckrock import foia

import logging

register = template.Library()

class TaskNode(template.Node):
    """A base class for rendering a task into a template."""
    model = task.models.Task
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

class OrphanTaskNode(TaskNode):
    """Renders an orphan task."""
    model = task.models.OrphanTask
    task_template = 'task/orphan.html'

class SnailMailTaskNode(TaskNode):
    """Renders a snail mail task."""
    model = task.models.SnailMailTask
    task_template = 'task/snail_mail.html'

    def get_extra_context(self, task):
        """Adds status to the context"""
        extra_context = super(SnailMailTaskNode, self).get_extra_context(task)
        extra_context['status'] = foia.models.STATUS
        return extra_context

class RejectedEmailTaskNode(TaskNode):
    """Renders a rejected email task."""
    model = task.models.RejectedEmailTask
    task_template = 'task/rejected_email.html'

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

def get_id(token):
    """Helper function to check token has correct arguments and return the task_id."""
    try:
        tag_name, task_id = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%s tag requires a single argument." % token.contents.split()[0])
    return task_id

@register.tag
def default_task(parser, token):
    """Returns the correct task node given a task ID"""
    return TaskNode(get_id(token))

@register.tag
def orphan_task(parser, token):
    """Returns an OrphanTaskNode"""
    return OrphanTaskNode(get_id(token))

@register.tag
def snail_mail_task(parser, token):
    """Returns a SnailMailTaskNode"""
    return SnailMailTaskNode(get_id(token))

@register.tag
def rejected_email_task(parser, token):
    """Returns a RejectedEmailTaskNode"""
    return RejectedEmailTaskNode(get_id(token))
