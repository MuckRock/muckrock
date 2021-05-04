"""
Nodes and tags for rendering tasks into templates
"""

# Django
from django import template
from django.conf import settings
from django.urls import reverse

# MuckRock
from muckrock import agency, foia, task
from muckrock.communication.forms import AddressForm
from muckrock.portal.forms import PortalForm
from muckrock.task.models import Task

register = template.Library()


class TaskNode(template.Node):
    """A base class for rendering a task into a template."""

    model = Task
    task_template = "task/default.html"
    endpoint_name = "task-list"
    class_name = "default"

    def __init__(self, task_):
        """The node should be initialized with a task object"""
        self._task = template.Variable(task_)
        self.task = None

    def render(self, context):
        """Render the task"""
        self.task = self._task.resolve(context)
        context.update(self.get_extra_context())
        templ = context.template.engine.get_template(self.task_template)
        return templ.render(context)

    def get_extra_context(self):
        """Returns a dictionary of context for the specific task"""
        endpoint_url = reverse(self.endpoint_name)
        extra_context = {
            "task": self.task,
            "class": self.class_name,
            "endpoint": endpoint_url,
        }
        return extra_context


class CrowdfundTaskNode(TaskNode):
    """Renders a crowdfund task."""

    model = task.models.CrowdfundTask
    task_template = "task/crowdfund.html"
    endpoint_name = "crowdfund-task-list"
    class_name = "crowdfund"

    def get_extra_context(self):
        """Adds the crowdfund object to context."""
        extra_context = super(CrowdfundTaskNode, self).get_extra_context()
        extra_context["crowdfund_object"] = self.task.crowdfund.get_crowdfund_object()
        return extra_context


class FlaggedTaskNode(TaskNode):
    """Renders a flagged task."""

    model = task.models.FlaggedTask
    task_template = "task/flagged.html"
    endpoint_name = "flagged-task-list"
    class_name = "flagged"

    def get_extra_context(self):
        """Adds a form for replying to the user"""
        extra_context = super(FlaggedTaskNode, self).get_extra_context()
        extra_context["flag_form"] = task.forms.FlaggedTaskForm()
        return extra_context


class ProjectReviewTaskNode(TaskNode):
    """Renders a flagged task."""

    model = task.models.ProjectReviewTask
    task_template = "task/project.html"
    endpoint_name = "projectreview-task-list"
    class_name = "project"

    def get_extra_context(self):
        """Adds a form for replying to the user"""
        extra_context = super(ProjectReviewTaskNode, self).get_extra_context()
        extra_context["form"] = task.forms.ProjectReviewTaskForm()
        return extra_context


class MultiRequestTaskNode(TaskNode):
    """Renders a multi-request task."""

    model = task.models.MultiRequestTask
    task_template = "task/multirequest.html"
    endpoint_name = "multirequest-task-list"
    class_name = "multirequest"


class NewAgencyTaskNode(TaskNode):
    """Renders a new agency task."""

    model = task.models.NewAgencyTask
    task_template = "task/new_agency.html"
    endpoint_name = "new-agency-task-list"
    class_name = "new-agency"

    def get_extra_context(self):
        """Adds an approval form, other agencies, and relevant requests to context"""
        extra_context = super(NewAgencyTaskNode, self).get_extra_context()
        emails = [
            e
            for e in self.task.agency.agencyemail_set.all()
            if e.email.status == "good"
            and e.request_type == "primary"
            and e.email_type == "to"
        ]
        phones = [
            p
            for p in self.task.agency.agencyphone_set.all()
            if p.phone.status == "good" and p.phone.type == "phone"
        ]
        faxes = [
            f
            for f in self.task.agency.agencyphone_set.all()
            if f.phone.status == "good"
            and f.phone.type == "fax"
            and f.request_type == "primary"
        ]
        addresses = [
            a
            for a in self.task.agency.agencyaddress_set.all()
            if a.request_type == "primary"
        ]
        initial = {
            "email": emails[0].email if emails else None,
            "phone": phones[0].phone if phones else None,
            "fax": faxes[0].phone if faxes else None,
        }
        if addresses:
            initial["address_suite"] = addresses[0].address.suite
            initial["address_street"] = addresses[0].address.street
            initial["address_city"] = addresses[0].address.city
            initial["address_state"] = addresses[0].address.state
            initial["address_zip"] = addresses[0].address.zip_code
        if self.task.agency.portal:
            initial["portal_url"] = self.task.agency.portal.url
            initial["portal_type"] = self.task.agency.portal.type
        extra_context["agency_form"] = agency.forms.AgencyForm(
            instance=self.task.agency, initial=initial, prefix=str(self.task.pk)
        )
        extra_context["replace_form"] = task.forms.ReplaceNewAgencyForm(
            initial={"replace_jurisdiction": self.task.agency.jurisdiction},
            prefix=str(self.task.pk),
        )
        extra_context["pending_drafts"] = self.task.agency.pending_drafts

        return extra_context


class OrphanTaskNode(TaskNode):
    """Renders an orphan task."""

    model = task.models.OrphanTask
    task_template = "task/orphan.html"
    endpoint_name = "orphan-task-list"
    class_name = "orphan"

    def get_extra_context(self):
        """Adds sender domain to the context"""
        extra_context = super(OrphanTaskNode, self).get_extra_context()
        extra_context["domain"] = self.task.get_sender_domain()
        extra_context["attachments"] = self.task.communication.files.all()
        return extra_context


class ResponseTaskNode(TaskNode):
    """Renders a response task."""

    model = task.models.ResponseTask
    task_template = "task/response.html"
    endpoint_name = "response-task-list"
    class_name = "response"

    def get_extra_context(self):
        """Adds ResponseTask-specific context"""
        extra_context = super(ResponseTaskNode, self).get_extra_context()
        form_initial = {}
        communication = self.task.communication
        predicted_status = self.task.predicted_status
        _foia = communication.foia
        if _foia:
            initial_status = predicted_status if predicted_status else _foia.status
            form_initial["status"] = initial_status
            form_initial["tracking_number"] = _foia.current_tracking_id()
            form_initial["date_estimate"] = _foia.date_estimate
            extra_context["previous_communications"] = _foia.reverse_communications
        extra_context["response_form"] = task.forms.ResponseTaskForm(
            initial=form_initial, task=self.task
        )
        extra_context["attachments"] = self.task.communication.files.all()
        return extra_context


class SnailMailTaskNode(TaskNode):
    """Renders a snail mail task."""

    model = task.models.SnailMailTask
    task_template = "task/snail_mail.html"
    endpoint_name = "snail-mail-task-list"
    class_name = "snail-mail"

    def get_extra_context(self):
        """Adds status to the context"""
        extra_context = super(SnailMailTaskNode, self).get_extra_context()
        extra_context["status"] = foia.models.STATUS
        # if this is an appeal and their is a specific appeal agency, display
        # that agency, else display the standard agency
        foia_ = self.task.communication.foia
        if self.task.category == "a" and foia_.agency.appeal_agency:
            agency_ = foia_.agency.appeal_agency
        else:
            agency_ = foia_.agency
        extra_context["agency"] = agency_
        extra_context["body"] = foia_.render_msg_body(
            comm=self.task.communication,
            switch=self.task.switch,
            appeal=self.task.category == "a",
        )
        extra_context["email"] = [str(e) for e in agency_.agencyemail_set.all()]
        extra_context["faxes"] = [
            str(f) for f in agency_.agencyphone_set.all() if f.phone.type == "fax"
        ]
        extra_context["phones"] = [
            str(p) for p in agency_.agencyphone_set.all() if p.phone.type == "phone"
        ]
        extra_context["addresses"] = [
            (str(a), a.address.lob_errors(agency_))
            for a in agency_.agencyaddress_set.all()
        ]

        def get_file_size(file_):
            """We will sometimes get an AttributeError when checking file sizes on S3
            This may be able to be changed when upgrading to the latest djang-storages
            """
            try:
                return file_.size
            except AttributeError:
                return None

        files = list(self.task.communication.files.all())
        extra_context["files"] = [
            (f.ffile.url, f.title, f.pages, get_file_size(f.ffile)) for f in files[:5]
        ]
        extra_context["files_length"] = len(files)

        return extra_context


class PortalTaskNode(TaskNode):
    """Renders a portal task."""

    model = task.models.PortalTask
    task_template = "task/portal.html"
    endpoint_name = "portal-task-list"
    class_name = "portal"

    def get_extra_context(self):
        """Get extra context"""
        extra_context = super(PortalTaskNode, self).get_extra_context()
        foia_ = self.task.communication.foia

        extra_context["return_address"] = (
            f"{settings.ADDRESS_NAME}\n"
            f"{settings.ADDRESS_DEPT}\n"
            f"{settings.ADDRESS_STREET}\n"
            f"{settings.ADDRESS_CITY}, {settings.ADDRESS_STATE} "
            f"{settings.ADDRESS_ZIP}".format(pk=foia_.pk if foia_ else "")
        )

        if self.task.category == "i":
            if foia_:
                form_initial = {
                    "status": foia_.status,
                    "tracking_number": foia_.current_tracking_id(),
                    "date_estimate": foia_.date_estimate,
                    "communication": self.task.communication.communication,
                    "word_to_pass": foia_.portal_password,
                }
                extra_context["previous_communications"] = foia_.reverse_communications[
                    :10
                ]
            else:
                form_initial = {}
            extra_context["form"] = task.forms.IncomingPortalForm(initial=form_initial)
            extra_context["attachments"] = self.task.communication.files.all()
        else:
            extra_context["status"] = foia.models.STATUS
            if foia_.portal and not foia_.portal_password:
                extra_context["password"] = foia_.portal.get_new_password()
            extra_context["reply_link"] = "https://{}{}".format(
                settings.MUCKROCK_URL,
                foia_.get_agency_reply_link(
                    email=foia_.email.email if foia_.email else None
                ),
            )

        return extra_context


class NewPortalTaskNode(TaskNode):
    """Renders a new portal task."""

    model = task.models.NewPortalTask
    task_template = "task/new_portal.html"
    endpoint_name = "new-portal-task-list"
    class_name = "new-portal"

    def get_extra_context(self):
        """Get extra context"""
        extra_context = super(NewPortalTaskNode, self).get_extra_context()

        extra_context["form"] = PortalForm(
            foia=self.task.communication.foia, initial={"type": self.task.portal_type}
        )

        return extra_context


class ReviewAgencyTaskNode(TaskNode):
    """Renders a review agency task."""

    model = task.models.ReviewAgencyTask
    task_template = "task/review_agency.html"
    endpoint_name = "review-agency-task-list"
    class_name = "review-agency"

    def get_extra_context(self):
        """Adds a form for updating the email"""
        extra_context = super(ReviewAgencyTaskNode, self).get_extra_context()
        email = [
            e.email
            for e in self.task.agency.agencyemail_set.all()
            if e.request_type == "primary"
            and e.email_type == "to"
            and e.email.status == "good"
        ]
        if email:
            initial = str(email[0])
        else:
            fax = [
                p.phone
                for p in self.task.agency.agencyphone_set.all()
                if p.request_type == "primary"
                and p.phone.type == "fax"
                and p.phone.status == "good"
            ]
            if fax:
                initial = str(fax[0])
            else:
                initial = ""
        followup_text = (
            "To Whom It May Concern:\n"
            "I wanted to follow up on the following request, copied below. "
            "Please let me know when I can expect to receive a response.\n"
            "Thanks for your help, and let me know if further "
            "clarification is needed."
        )
        extra_context["form"] = task.forms.ReviewAgencyTaskForm(
            initial={
                "email_or_fax": initial,
                "update_agency_info": not initial,
                "reply": followup_text,
            },
            prefix=str(self.task.pk),
        )
        return extra_context


class StatusChangeTaskNode(TaskNode):
    """Renders a status change task."""

    model = task.models.StatusChangeTask
    task_template = "task/status_change.html"
    endpoint_name = "status-change-task-list"
    class_name = "status-change"


class PaymentInfoTaskNode(TaskNode):
    """Renders a payment info task."""

    model = task.models.SnailMailTask
    task_template = "task/payment_info.html"
    endpoint_name = "payment-info-task-list"
    class_name = "payment-info"

    def get_extra_context(self):
        """Adds status to the context"""
        foia_ = self.task.communication.foia
        extra_context = super(PaymentInfoTaskNode, self).get_extra_context()
        extra_context["form"] = AddressForm(agency=foia_.agency)
        extra_context["previous_communications"] = foia_.reverse_communications
        return extra_context


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#


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
def portal_task(parser, token):
    """Returns a PortalTaskNode"""
    return PortalTaskNode(get_id(token))


@register.tag
def new_portal_task(parser, token):
    """Returns a NewPortalTaskNode"""
    return NewPortalTaskNode(get_id(token))


@register.tag
def review_agency_task(parser, token):
    """Returns a ReviewAgencyTaskNode"""
    return ReviewAgencyTaskNode(get_id(token))


@register.tag
def flagged_task(parser, token):
    """Returns a FlaggedTaskNode"""
    return FlaggedTaskNode(get_id(token))


@register.tag
def project_review_task(parser, token):
    """Returns a ProjectReviewTaskNode"""
    return ProjectReviewTaskNode(get_id(token))


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
def crowdfund_task(parser, token):
    """Returns a CrowdfundTaskNode"""
    return CrowdfundTaskNode(get_id(token))


@register.tag
def payment_info_task(parser, token):
    """Returns a PaymentInfoTaskNode"""
    return PaymentInfoTaskNode(get_id(token))


@register.tag
def multi_request_task(parser, token):
    """Returns a MultiRequestTaskNode"""
    return MultiRequestTaskNode(get_id(token))
