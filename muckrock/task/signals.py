"""Signals for the task application"""
# Django
from django.db.models.signals import post_save
from django.urls import reverse

# Standard Library
import logging

# MuckRock
from muckrock.message.tasks import slack
from muckrock.message.utils import format_user, slack_attachment, slack_message
from muckrock.task.models import (
    BlacklistDomain,
    FlaggedTask,
    OrphanTask,
    ProjectReviewTask,
)
from muckrock.task.tasks import create_ticket

logger = logging.getLogger(__name__)

# pylint: disable=unused-argument


def domain_blacklist(sender, instance, created, **kwargs):
    """Blacklist certain domains - automatically reject tasks from them"""
    if not created:
        # if this isn't being created for the first time, just return
        # to avoid an infinite loop from when we resolve the task
        return
    domain = instance.get_sender_domain()
    if domain is None:
        return
    logger.info("Checking domain %s against blacklist", domain)
    if BlacklistDomain.objects.filter(domain=domain).exists():
        instance.resolve()
    return


def notify_flagged(sender, instance, created, **kwargs):
    """When a new flagged task is created, send a Slack notification."""

    def create_flagged_task_payload(flagged_task):
        """Create a Slack notification payload for a Flagged Task"""
        base_url = "https://www.muckrock.com"
        task_url = base_url + reverse("flagged-task", args=(flagged_task.id,))
        fields = []
        if flagged_task.user is not None:
            flagged_by = slack_attachment("Flagged by", format_user(flagged_task.user))
            fields.append(flagged_by)
        flagged_object = {
            "title": "%s" % flagged_task.flagged_object().__class__.__name__,
            "value": "<%(url)s|%(name)s>"
            % {
                "url": base_url + flagged_task.flagged_object().get_absolute_url(),
                "name": str(flagged_task.flagged_object()),
            },
            "short": True,
        }
        fields.append(flagged_object)
        summary = "New <%(task_url)s|flagged task>: %(text)s" % {
            "task_url": task_url,
            "text": flagged_task.text,
        }
        attachments = [
            {"fallback": summary, "text": flagged_task.text, "fields": fields}
        ]
        return slack_message(
            ":triangular_flag_on_post:",
            "#tasks",
            "New <%s|flagged task>" % task_url,
            attachments,
        )

    if not created or kwargs.get("raw", False):
        # the raw test prevents text fixtures from creating any notifications
        return
    payload = create_flagged_task_payload(instance)
    slack.delay(payload)


def notify_project(sender, instance, created, **kwargs):
    """When a new project task is created, send a Slack notification."""

    def create_project_task_payload(task):
        """Create a Slack notification payload for a Project Review Task."""
        base_url = "https://www.muckrock.com"
        task_url = base_url + reverse("projectreview-task", args=(task.id,))
        project_url = base_url + task.project.get_absolute_url()
        summary = "<%(url)s|%(title)s> was submitted for review." % {
            "url": project_url,
            "title": task.project.title,
        }
        names = [
            format_user(contributor) for contributor in task.project.contributors.all()
        ]
        contributors = ", ".join(names)
        fields = [slack_attachment("Contributors", contributors)]
        if task.notes:
            fields.append(slack_attachment("Note", task.notes))
        attachments = [{"fallback": summary, "text": summary, "fields": fields}]
        return slack_message(
            ":file_cabinet:",
            "#tasks",
            "New <%s|pending project>" % task_url,
            attachments,
        )

    if not created or kwargs.get("raw", False):
        # the raw test prevents text fixtures from creating any notifications
        return
    payload = create_project_task_payload(instance)
    slack.delay(payload)


def flagged(sender, instance, created, **kwargs):
    """Create a ticket after creation"""
    # pylint: disable=unused-argument
    if created:
        create_ticket.delay(instance.pk)


post_save.connect(
    domain_blacklist,
    sender=OrphanTask,
    dispatch_uid="muckrock.task.signals.domain_blacklist",
)
post_save.connect(
    notify_flagged,
    sender=FlaggedTask,
    dispatch_uid="muckrock.task.signals.notify_flagged",
)
post_save.connect(
    notify_project,
    sender=ProjectReviewTask,
    dispatch_uid="muckrock.task.signals.notify_project",
)
post_save.connect(
    flagged, sender=FlaggedTask, dispatch_uid="muckrock.task.signals.flagged"
)
