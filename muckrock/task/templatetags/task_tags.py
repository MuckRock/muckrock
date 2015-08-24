"""
Nodes and tags for rendering tasks into templates
"""

from django import template
from django.core.urlresolvers import reverse

from muckrock import agency
from muckrock import foia
from muckrock import task
# imports Task model separately to patch bug in django-compressor parser
from muckrock.task.models import Task

register = template.Library()

class TaskNode(template.Node):
    """A base class for rendering a task into a template."""
    model = Task
    task_template = 'task/default.html'
    endpoint_name = 'task-list'

    def __init__(self, task_id):
        """The node should be initialized with a task object"""
        self.task_id = template.Variable(task_id)

    def render(self, context):
        """Render the task"""
        try:
            the_task = self.model.objects.get(id=self.task_id.resolve(context))
        except (template.VariableDoesNotExist, self.model.DoesNotExist):
            return ''
        context.update(self.get_extra_context(the_task))
        return template.loader.render_to_string(self.task_template, context)

    def get_extra_context(self, the_task):
        """Returns a dictionary of context for the specific task"""
        endpoint_url = reverse(self.endpoint_name)
        extra_context = {'task': the_task, 'endpoint': endpoint_url}
        return extra_context

class OrphanTaskNode(TaskNode):
    """Renders an orphan task."""
    model = task.models.OrphanTask
    task_template = 'task/orphan.html'
    endpoint_name = 'orphan-task-list'

    def get_extra_context(self, the_task):
        """Adds sender domain to the context"""
        extra_context = super(OrphanTaskNode, self).get_extra_context(the_task)
        extra_context['domain'] = the_task.get_sender_domain()
        return extra_context

class SnailMailTaskNode(TaskNode):
    """Renders a snail mail task."""
    model = task.models.SnailMailTask
    task_template = 'task/snail_mail.html'
    endpoint_name = 'snail-mail-task-list'

    def get_extra_context(self, the_task):
        """Adds status to the context"""
        extra_context = super(SnailMailTaskNode, self).get_extra_context(the_task)
        extra_context['status'] = foia.models.STATUS
        return extra_context

class RejectedEmailTaskNode(TaskNode):
    """Renders a rejected email task."""
    model = task.models.RejectedEmailTask
    task_template = 'task/rejected_email.html'
    endpoint_name = 'rejected-email-task-list'

class StaleAgencyTaskNode(TaskNode):
    """Renders a stale agency task."""
    model = task.models.StaleAgencyTask
    task_template = 'task/stale_agency.html'
    endpoint_name = 'stale-agency-task-list'

class FlaggedTaskNode(TaskNode):
    """Renders a flagged task."""
    model = task.models.FlaggedTask
    task_template = 'task/flagged.html'
    endpoint_name = 'flagged-task-list'

class StatusChangeTaskNode(TaskNode):
    """Renders a status change task."""
    model = task.models.StatusChangeTask
    task_template = 'task/status_change.html'
    endpoint_name = 'status-change-task-list'

class PaymentTaskNode(TaskNode):
    """Renders a payment task."""
    model = task.models.PaymentTask
    task_template = 'task/payment.html'
    endpoint_name = 'payment-task-list'

class CrowdfundTaskNode(TaskNode):
    """Renders a crowdfund task."""
    model = task.models.GenericCrowdfundTask
    task_template = 'task/crowdfund.html'
    endpoint_name = 'crowdfund-task-list'

class MultiRequestTaskNode(TaskNode):
    """Renders a multi-request task."""
    model = task.models.MultiRequestTask
    task_template = 'task/multirequest.html'
    endpoint_name = 'multirequest-task-list'

class FailedFaxTaskNode(TaskNode):
    """Renders a failed fax task."""
    model = task.models.FailedFaxTask
    task_template = 'task/failed_fax.html'
    endpoint_name = 'failed-fax-task-list'

class NewAgencyTaskNode(TaskNode):
    """Renders a new agency task."""
    model = task.models.NewAgencyTask
    task_template = 'task/new_agency.html'
    endpoint_name = 'new-agency-task-list'

    def get_extra_context(self, the_task):
        """Adds an approval form, other agencies, and relevant requests to context"""
        # pylint:disable=line-too-long
        extra_context = super(NewAgencyTaskNode, self).get_extra_context(the_task)
        other_agencies = agency.models.Agency.objects.filter(jurisdiction=the_task.agency.jurisdiction)
        other_agencies = other_agencies.exclude(id=the_task.agency.id)
        other_agencies = other_agencies.order_by('name')
        extra_context['agency_form'] = agency.forms.AgencyForm(instance=the_task.agency)
        extra_context['other_agencies'] = other_agencies
        extra_context['foias'] = foia.models.FOIARequest.objects.filter(agency=the_task.agency)
        return extra_context

class ResponseTaskNode(TaskNode):
    """Renders a response task."""
    model = task.models.ResponseTask
    task_template = 'task/response.html'
    endpoint_name = 'response-task-list'

    def get_extra_context(self, the_task):
        """Adds ResponseTask-specific context"""
        extra_context = super(ResponseTaskNode, self).get_extra_context(the_task)
        form_initial = {}
        if the_task.communication.foia:
            the_foia = the_task.communication.foia
            form_initial['status'] = the_foia.status
            form_initial['tracking_number'] = the_foia.tracking_id
            extra_context['all_comms'] = the_foia.communications.all().order_by('-date')
        extra_context['response_form'] = task.forms.ResponseTaskForm(initial=form_initial)
        extra_context['attachments'] = the_task.communication.files.all()
        return extra_context

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

def get_id(token):
    """Helper function to check token has correct arguments and return the task_id."""
    # pylint:disable=unused-variable
    try:
        tag_name, task_id = token.split_contents()
    except ValueError:
        error_msg = "%s tag requires a single argument." % token.contents.split()[0]
        raise template.TemplateSyntaxError(error_msg)
    return task_id

# pylint:disable=unused-argument

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

@register.tag
def status_change_task(parser, token):
    """Returns a StatusChangeTaskNode"""
    return StatusChangeTaskNode(get_id(token))

@register.tag
def payment_task(parser, token):
    """Returns a PaymentTaskNode"""
    return PaymentTaskNode(get_id(token))

@register.tag
def crowdfund_task(parser, token):
    """Returns a CrowdfundTaskNode"""
    return CrowdfundTaskNode(get_id(token))

@register.tag
def multi_request_task(parser, token):
    """Returns a MultiRequestTaskNode"""
    return MultiRequestTaskNode(get_id(token))

@register.tag
def failed_fax_task(parser, token):
    """Returns a FailedFaxTaskNode"""
    return FailedFaxTaskNode(get_id(token))
