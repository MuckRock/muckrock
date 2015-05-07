from django import template

from muckrock import agency
from muckrock import foia
from muckrock import task


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

class StaleAgencyTaskNode(TaskNode):
    """Renders a stale agency task."""
    model = task.models.StaleAgencyTask
    task_template = 'task/stale_agency.html'

class FlaggedTaskNode(TaskNode):
    """Renders a flagged task."""
    model = task.models.FlaggedTask
    task_template = 'task/flagged.html'

class NewAgencyTaskNode(TaskNode):
    """Renders a new agency task."""
    model = task.models.NewAgencyTask
    task_template = 'task/new_agency.html'

    def get_extra_context(self, task):
        """Adds an approval form, other agencies, and relevant requests to context"""
        extra_context = super(NewAgencyTaskNode, self).get_extra_context(task)
        other_agencies = agency.models.Agency.objects.filter(jurisdiction=task.agency.jurisdiction)
        other_agencies = other_agencies.exclude(id=task.agency.id)
        extra_context['agency_form'] = agency.forms.AgencyForm(instance=task.agency)
        extra_context['other_agencies'] = other_agencies
        extra_context['foias'] = foia.models.FOIARequest.objects.filter(agency=task.agency)
        return extra_context

class ResponseTaskNode(TaskNode):
    """Renders a response task."""
    mdoel = task.models.ResponseTask
    task_template = 'task/response.html'

    def get_extra_context(self, task):
        """Adds ResponseTask-specific context"""
        extra_context = super(ResponseTaskNode, self).get_extra_context(task)
        form_initial = {}
        if task.communication.foia:
            the_foia = task.communication.foia
            form_initial['status'] = the_foia.status
            form_initial['tracking_number'] = the_foia.tracking_id
            extra_context['all_comms'] = the_foia.communications.all().order_by('-date')
        extra_context['response_form'] = ResponseTaskForm(initial=form_initial)
        extra_context['attachments'] = task.communication.files.all()
        return extra_context

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

@register.tag
def stale_agency_task(parser, token):
    """Returns a StaleAgencyTaskNode"""
    return StaleAgencyTaskNode(get_id(token))

@register.tag
def flagged_task(parser, token):
    """Returns a FlaggedTaskNode"""
    return FlaggedTaskNode(get_id(token))

@register.tag
def new_agency_task(parser, token):
    """Returns a NewAgencyTaskNode"""
    return NewAgencyTaskNode(get_id(token))

@register.tag
def response_task(parser, token):
    """Returns a ResponseTaskNode"""
    return ResponseTaskNode(get_id(token))
