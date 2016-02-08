"""
Nodes and tags for rendering tasks into templates
"""

from django import template
from django.core.urlresolvers import reverse

from muckrock import agency, foia, task
# imports Task model separately to patch bug in django-compressor parser
from muckrock.task.models import Task

 # pylint:disable=no-member

register = template.Library()

class TaskNode(template.Node):
    """A base class for rendering a task into a template."""
    model = Task
    task_template = 'task/default.html'
    endpoint_name = 'task-list'
    class_name = 'default'

    def __init__(self, task_):
        """The node should be initialized with a task object"""
        self._task = template.Variable(task_)
        self.task = None

    def render(self, context):
        """Render the task"""
        self.task = self._task.resolve(context)
        context.update(self.get_extra_context())
        return template.loader.render_to_string(self.task_template, context)

    def get_extra_context(self):
        """Returns a dictionary of context for the specific task"""
        endpoint_url = reverse(self.endpoint_name)
        extra_context = {
            'task': self.task,
            'class': self.class_name,
            'endpoint': endpoint_url
        }
        return extra_context


class CrowdfundTaskNode(TaskNode):
    """Renders a crowdfund task."""
    model = task.models.GenericCrowdfundTask
    task_template = 'task/crowdfund.html'
    endpoint_name = 'crowdfund-task-list'
    class_name = 'crowdfund'


class FailedFaxTaskNode(TaskNode):
    """Renders a failed fax task."""
    model = task.models.FailedFaxTask
    task_template = 'task/failed_fax.html'
    endpoint_name = 'failed-fax-task-list'
    class_name = 'failed-fax'


class FlaggedTaskNode(TaskNode):
    """Renders a flagged task."""
    model = task.models.FlaggedTask
    task_template = 'task/flagged.html'
    endpoint_name = 'flagged-task-list'
    class_name = 'flagged'

    def get_extra_context(self):
        """Adds a form for replying to the user"""
        extra_context = super(FlaggedTaskNode, self).get_extra_context()
        extra_context['flag_form'] = task.forms.FlaggedTaskForm()
        return extra_context


class MultiRequestTaskNode(TaskNode):
    """Renders a multi-request task."""
    model = task.models.MultiRequestTask
    task_template = 'task/multirequest.html'
    endpoint_name = 'multirequest-task-list'
    class_name = 'multirequest'


class NewAgencyTaskNode(TaskNode):
    """Renders a new agency task."""
    model = task.models.NewAgencyTask
    task_template = 'task/new_agency.html'
    endpoint_name = 'new-agency-task-list'
    class_name = 'new-agency'

    def get_extra_context(self):
        """Adds an approval form, other agencies, and relevant requests to context"""
        extra_context = super(NewAgencyTaskNode, self).get_extra_context()
        extra_context['agency_form'] = agency.forms.AgencyForm(instance=self.task.agency)
        return extra_context


class OrphanTaskNode(TaskNode):
    """Renders an orphan task."""
    model = task.models.OrphanTask
    task_template = 'task/orphan.html'
    endpoint_name = 'orphan-task-list'
    class_name = 'orphan'

    def get_extra_context(self):
        """Adds sender domain to the context"""
        # pylint:disable=no-member
        extra_context = super(OrphanTaskNode, self).get_extra_context()
        extra_context['domain'] = self.task.get_sender_domain()
        extra_context['attachments'] = self.task.communication.files.all()
        return extra_context


class PaymentTaskNode(TaskNode):
    """Renders a payment task."""
    model = task.models.PaymentTask
    task_template = 'task/payment.html'
    endpoint_name = 'payment-task-list'
    class_name = 'payment'


class RejectedEmailTaskNode(TaskNode):
    """Renders a rejected email task."""
    model = task.models.RejectedEmailTask
    task_template = 'task/rejected_email.html'
    endpoint_name = 'rejected-email-task-list'
    class_name = 'rejected-email'

class ResponseTaskNode(TaskNode):
    """Renders a response task."""
    model = task.models.ResponseTask
    task_template = 'task/response.html'
    endpoint_name = 'response-task-list'
    class_name = 'response'

    def get_extra_context(self):
        """Adds ResponseTask-specific context"""
        extra_context = super(ResponseTaskNode, self).get_extra_context()
        form_initial = {}
        communication = self.task.communication
        _foia = communication.foia
        if _foia:
            form_initial['status'] = _foia.status
            form_initial['tracking_number'] = _foia.tracking_id
            form_initial['date_estimate'] = _foia.date_estimate
            extra_context['previous_communications'] = _foia.reverse_communications
        extra_context['response_form'] = task.forms.ResponseTaskForm(initial=form_initial)
        extra_context['attachments'] = self.task.communication.files.all()
        return extra_context


class SnailMailTaskNode(TaskNode):
    """Renders a snail mail task."""
    model = task.models.SnailMailTask
    task_template = 'task/snail_mail.html'
    endpoint_name = 'snail-mail-task-list'
    class_name = 'snail-mail'

    def get_extra_context(self):
        """Adds status to the context"""
        extra_context = super(SnailMailTaskNode, self).get_extra_context()
        extra_context['status'] = foia.models.STATUS
        return extra_context


class StaleAgencyTaskNode(TaskNode):
    """Renders a stale agency task."""
    model = task.models.StaleAgencyTask
    task_template = 'task/stale_agency.html'
    endpoint_name = 'stale-agency-task-list'
    class_name = 'stale-agency'


class StatusChangeTaskNode(TaskNode):
    """Renders a status change task."""
    model = task.models.StatusChangeTask
    task_template = 'task/status_change.html'
    endpoint_name = 'status-change-task-list'
    class_name = 'status-change'


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
