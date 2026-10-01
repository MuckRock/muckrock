# -*- coding: utf-8 -*-
"""
Tests for task querysets
"""

# Django
from django.test import RequestFactory, TestCase
from django.urls import reverse

# Standard Library
import time

# MuckRock
from muckrock.communication.factories import EmailAddressFactory
from muckrock.communication.models import EmailAddress
from muckrock.core.factories import AgencyFactory
from muckrock.foia.factories import FOIACommunicationFactory
from muckrock.mailgun.tests import TestMailgunViews
from muckrock.mailgun.views import bounces
from muckrock.task.factories import ReviewAgencyTaskFactory
from muckrock.task.models import ReviewAgencyTask


class TestReviewAgencyTaskQuerySet(TestCase):
    """Test that review agency tasks are scoped to a single channel

    A task's job is to say what is broken.  Keyed on (agency, source) alone it
    cannot: every broken mailbox at an agency collapses into one row, so a
    staffer fixes one address while the others keep failing.  Adding the
    channel to the key is what makes a task repairable.
    """

    def setUp(self):
        self.agency = AgencyFactory()

    def test_distinct_channels_get_distinct_tasks(self):
        """Two broken mailboxes at one agency are two tasks"""
        first = EmailAddressFactory()
        second = EmailAddressFactory()
        task_one = ReviewAgencyTask.objects.ensure_one_created(
            agency=self.agency, resolved=False, source="email", email=first
        )
        task_two = ReviewAgencyTask.objects.ensure_one_created(
            agency=self.agency, resolved=False, source="email", email=second
        )
        assert task_one.pk != task_two.pk
        assert ReviewAgencyTask.objects.filter(agency=self.agency).count() == 2

    def test_same_channel_is_idempotent(self):
        """Repeating a call for the same channel reuses the task"""
        address = EmailAddressFactory()
        first = ReviewAgencyTask.objects.ensure_one_created(
            agency=self.agency, resolved=False, source="email", email=address
        )
        second = ReviewAgencyTask.objects.ensure_one_created(
            agency=self.agency, resolved=False, source="email", email=address
        )
        assert first.pk == second.pk
        assert ReviewAgencyTask.objects.filter(agency=self.agency).count() == 1

    def test_null_channel_still_dedupes(self):
        """staff and stale tasks are about the agency, so they stay agency level"""
        first = ReviewAgencyTask.objects.ensure_one_created(
            agency=self.agency, resolved=False, source="staff"
        )
        second = ReviewAgencyTask.objects.ensure_one_created(
            agency=self.agency, resolved=False, source="staff"
        )
        assert first.pk == second.pk
        assert first.email is None

    def test_null_channel_task_coexists_with_channel_tasks(self):
        """An agency level task does not absorb a channel task"""
        address = EmailAddressFactory()
        agency_task = ReviewAgencyTask.objects.ensure_one_created(
            agency=self.agency, resolved=False, source="stale"
        )
        channel_task = ReviewAgencyTask.objects.ensure_one_created(
            agency=self.agency, resolved=False, source="email", email=address
        )
        assert agency_task.pk != channel_task.pk

    def test_preexisting_duplicates_collapse(self):
        """The MultipleObjectsReturned recovery path still works per channel"""
        address = EmailAddressFactory()
        ReviewAgencyTaskFactory.create_batch(
            3, agency=self.agency, resolved=False, source="email", email=address
        )
        task = ReviewAgencyTask.objects.ensure_one_created(
            agency=self.agency, resolved=False, source="email", email=address
        )
        remaining = ReviewAgencyTask.objects.filter(
            agency=self.agency, resolved=False, email=address
        )
        assert remaining.count() == 1
        assert remaining.get().pk == task.pk

    def test_duplicate_collapse_leaves_other_channels_alone(self):
        """Collapsing duplicates on one channel does not touch another"""
        address = EmailAddressFactory()
        other = EmailAddressFactory()
        ReviewAgencyTaskFactory.create_batch(
            2, agency=self.agency, resolved=False, source="email", email=address
        )
        keeper = ReviewAgencyTaskFactory(
            agency=self.agency, resolved=False, source="email", email=other
        )
        ReviewAgencyTask.objects.ensure_one_created(
            agency=self.agency, resolved=False, source="email", email=address
        )
        assert ReviewAgencyTask.objects.filter(pk=keeper.pk).exists()


class TestBounceCreatesChannelTask(TestMailgunViews):
    """A bounce carries the broken address into the task it creates"""

    def bounce(self, foia, recipient):
        """Post a bounce webhook for one address on one request"""
        comm = foia.communications.first()
        email_comm = comm.emails.first()
        signature = {}
        self.sign(signature)
        data = {
            "event-data": {
                "event": "failed",
                "timestamp": int(time.time()),
                "severity": "permanent",
                "recipient": recipient,
                "delivery-status": {"code": 550, "description": "no such mailbox"},
                "user-variables": {"email_id": email_comm.pk},
            },
            "signature": signature,
        }
        request = RequestFactory().post(
            reverse("mailgun-bounces"), data, content_type="application/json"
        )
        bounces(request)  # pylint: disable=no-value-for-parameter

    def test_casing_on_the_wire_yields_one_task(self):
        """A bounce for any casing lands on the one normalized channel"""
        address = EmailAddress.objects.fetch("foipaquestions@fbi.gov")
        comm = FOIACommunicationFactory(foia__email=address, foia__agency__fax=None)
        agency = comm.foia.agency

        self.bounce(comm.foia, "FOIPAQUESTIONS@fbi.gov")
        self.bounce(comm.foia, "foipaquestions@fbi.gov")

        tasks = ReviewAgencyTask.objects.filter(agency=agency, source="email")
        assert tasks.count() == 1
        assert tasks.get().email == address

    def test_a_second_mailbox_creates_a_second_task(self):
        """A genuinely different address at the same agency is its own task"""
        first = EmailAddress.objects.fetch("foia@fbi.gov")
        comm_one = FOIACommunicationFactory(foia__email=first, foia__agency__fax=None)
        agency = comm_one.foia.agency
        second = EmailAddress.objects.fetch("records@fbi.gov")
        comm_two = FOIACommunicationFactory(foia__email=second, foia__agency=agency)

        self.bounce(comm_one.foia, "foia@fbi.gov")
        self.bounce(comm_two.foia, "records@fbi.gov")

        tasks = ReviewAgencyTask.objects.filter(agency=agency, source="email")
        assert tasks.count() == 2
        assert {t.email for t in tasks} == {first, second}
