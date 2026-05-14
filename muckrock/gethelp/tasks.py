"""Celery tasks for the gethelp app"""

# Django
from celery import shared_task
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone

# Standard Library
import logging
import sys
from random import randint

# Third Party
from requests.exceptions import RequestException
from zenpy.lib.exception import APIException, ZenpyException

# MuckRock
from muckrock.core.utils import create_zendesk_ticket
from muckrock.foia.models import FOIARequest
from muckrock.organization.models import Membership

logger = logging.getLogger(__name__)

MR_NUMBER_FIELD = 1500004565182


def create_ticket_subject(user, category_label, problem_title):
    username = user.username if user else "anonymous"
    if category_label and problem_title:
        subject = f"[{category_label}] {problem_title} @{username}"
    elif category_label:
        subject = f"[{category_label}] @{username}"
    else:
        subject = f"[GetHelp] @{username}"
    return subject


def create_ticket_description(text, user, foia):
    description = text
    if foia:
        description += f"\n\nRequest: {settings.MUCKROCK_URL}{foia.get_absolute_url()}"
    if user:
        description += (
            f"\nUser profile: {settings.MUCKROCK_URL}{user.profile.get_absolute_url()}"
        )
        for org in user.organizations.filter(individual=False):
            plan = "Premium" if org.entitlement.base_requests > 0 else "Free"
            description += (
                f"\nOrg: {settings.MUCKROCK_URL}{org.get_absolute_url()} ({plan})"
            )
    return description


def create_ticket_tags(category_label):
    tags = ["gethelp"]
    if category_label:
        tags.append(category_label.lower().replace(" ", "_"))
    return tags


def create_ticket_data(user, foia):
    if user:
        requester_data = {
            "name": user.profile.full_name or user.username,
            "external_id": str(user.profile.uuid),
        }
        if user.email:
            requester_data["email"] = user.email
        if foia:
            primary_org = foia.composer.organization
        else:
            try:
                primary_org = user.profile.organization
            except Membership.DoesNotExist:
                primary_org = None
        if primary_org:
            org_data = {
                "name": primary_org.name,
                "external_id": str(primary_org.uuid),
            }
        else:
            org_data = None
    else:
        requester_data = {"name": "Anonymous User"}
        org_data = None
    return [requester_data, org_data]


@shared_task(ignore_result=True, max_retries=5)
def create_gethelp_ticket(
    user_pk, text, foia_pk=None, category_label="", problem_title=""
):
    """Create a Zendesk support ticket from a GetHelp form submission."""
    user = (
        User.objects.filter(pk=user_pk).select_related("profile").first()
        if user_pk
        else None
    )
    foia = FOIARequest.objects.filter(pk=foia_pk).first() if foia_pk else None
    [requester_data, org_data] = create_ticket_data(user, foia)
    custom_fields = [{"id": MR_NUMBER_FIELD, "value": foia.pk}] if foia else None

    try:
        ticket_id = create_zendesk_ticket(
            subject=create_ticket_subject(user, category_label, problem_title),
            description=create_ticket_description(text, user, foia),
            tags=create_ticket_tags(category_label),
            requester_data=requester_data,
            org_data=org_data,
            custom_fields=custom_fields,
        )
        if foia and user and foia.has_perm(user, "change"):
            foia.notes.create(
                author=user,
                datetime=timezone.now(),
                note=f"Submitted help request:\n\n{text}\n\n" f"Ticket ID: {ticket_id}",
            )
    except (RequestException, ZenpyException, APIException) as exc:
        logger.warning(
            "Zendesk error in create_gethelp_ticket: %s", exc, exc_info=sys.exc_info()
        )
        raise create_gethelp_ticket.retry(
            countdown=(2**create_gethelp_ticket.request.retries) * 300
            + randint(0, 300),
            exc=exc,
        )
