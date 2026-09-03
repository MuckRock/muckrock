# -*- coding: utf-8 -*-
"""
Tests for the resolved task readout

Today the resolved view hides the interesting parts.  A resolve that did not
hold is a signal, not noise: the queue grows by roughly 20 newly blocked
requests a day, so knowing which repairs stuck is how staff avoid repeating
work that already failed.
"""

# Django
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

# Standard Library
from datetime import timedelta

# MuckRock
from muckrock.communication.factories import EmailAddressFactory
from muckrock.core.factories import AgencyFactory, UserFactory
from muckrock.foia.factories import FOIACommunicationFactory, FOIARequestFactory
from muckrock.task.factories import ReviewAgencyTaskFactory
from muckrock.task.models import ReviewAgencyTask


class ResolvedReadoutMixin:
    """Shared setup"""

    # pylint: disable=invalid-name
    def setUp(self):
        password = "abc"
        self.user = UserFactory(is_staff=True, password=password)
        self.agency = AgencyFactory(email=None, fax=None)
        self.address = EmailAddressFactory(email="old@agency.gov", status="error")
        self.client.login(username=self.user.username, password=password)

    def resolved_task(self, days_ago=5, **outcome):
        """A task resolved with a repair outcome recorded"""
        task = ReviewAgencyTaskFactory(
            agency=self.agency, source="email", email=self.address
        )
        payload = {
            "old_email": "old@agency.gov",
            "new_email": "new@agency.gov",
            "requests_updated": 3,
            "followup_sent": True,
            "agency_info_updated": True,
            "snail_mail": False,
            "by": self.user.username,
            "at": timezone.now().isoformat(),
        }
        payload.update(outcome)
        task.resolve(self.user, {"repair": payload})
        ReviewAgencyTask.objects.filter(pk=task.pk).update(
            date_done=timezone.now() - timedelta(days=days_ago)
        )
        task.refresh_from_db()
        return task


class TestResolvedOutcome(ResolvedReadoutMixin, TestCase):
    """What was done, in one line"""

    def test_outcome_fields_are_available(self):
        """Channel, old to new, count, follow up, by whom, when"""
        task = self.resolved_task()
        outcome = task.repair_outcome
        assert outcome["old_email"] == "old@agency.gov"
        assert outcome["new_email"] == "new@agency.gov"
        assert outcome["requests_updated"] == 3
        assert outcome["followup_sent"] is True
        assert outcome["by"] == self.user.username

    def render(self, task):
        """The rendered page for one task"""
        response = self.client.get(
            reverse("review-agency-task", kwargs={"pk": task.pk})
        )
        assert response.status_code == 200
        return response.content.decode()

    def test_resolved_view_renders_a_readout_not_a_dict_dump(self):
        """One legible line, not the raw form_data table

        The generic table stringifies the whole payload, which is the "resolved
        view hides the interesting parts" complaint in #1869 and #1870.
        """
        content = self.render(self.resolved_task())
        assert "review-agency-outcome" in content
        assert "old@agency.gov" in content
        assert "new@agency.gov" in content
        assert "3 request" in content
        assert "Follow-up sent" in content
        assert self.user.username in content

    def test_readout_says_when_no_contact_change_was_made(self):
        """Resolving because nothing was broken reads differently"""
        content = self.render(
            self.resolved_task(new_email=None, requests_updated=0, followup_sent=False)
        )
        assert "No contact change" in content

    def test_readout_reports_it_held(self):
        """A response since the resolve is the evidence the repair worked"""
        task = self.resolved_task(days_ago=10)
        foia = FOIARequestFactory(agency=self.agency, status="ack")
        FOIACommunicationFactory(
            foia=foia, response=True, datetime=timezone.now() - timedelta(days=2)
        )
        assert "Held" in self.render(task)

    def test_readout_reports_unverified(self):
        """Nothing back yet, so we do not claim it worked"""
        assert "Not verified" in self.render(self.resolved_task(days_ago=10))

    def test_readout_links_a_reopen(self):
        """A resolve that did not hold links forward to the new task"""
        task = self.resolved_task()
        successor = ReviewAgencyTaskFactory(
            agency=self.agency, source="email", email=self.address, resolved=False
        )
        content = self.render(task)
        assert "Reopened" in content
        assert successor.get_absolute_url() in content


class TestDidItHold(ResolvedReadoutMixin, TestCase):
    """Whether the repair actually worked"""

    def test_a_response_after_the_resolve_reads_as_held(self):
        """The agency has communicated with us since"""
        task = self.resolved_task(days_ago=10)
        foia = FOIARequestFactory(agency=self.agency, status="ack")
        FOIACommunicationFactory(
            foia=foia,
            response=True,
            datetime=timezone.now() - timedelta(days=2),
        )
        annotated = ReviewAgencyTask.objects.with_outcome().get(pk=task.pk)
        assert annotated.held

    def test_no_response_since_reads_as_unverified(self):
        """Nothing has come back, so we cannot say it worked"""
        task = self.resolved_task(days_ago=10)
        annotated = ReviewAgencyTask.objects.with_outcome().get(pk=task.pk)
        assert not annotated.held

    def test_a_response_before_the_resolve_does_not_count(self):
        """Old traffic is not evidence that this repair held"""
        task = self.resolved_task(days_ago=10)
        foia = FOIARequestFactory(agency=self.agency, status="ack")
        FOIACommunicationFactory(
            foia=foia,
            response=True,
            datetime=timezone.now() - timedelta(days=30),
        )
        annotated = ReviewAgencyTask.objects.with_outcome().get(pk=task.pk)
        assert not annotated.held

    def test_an_outgoing_message_does_not_count(self):
        """Us mailing them is not the agency responding"""
        task = self.resolved_task(days_ago=10)
        foia = FOIARequestFactory(agency=self.agency, status="ack")
        FOIACommunicationFactory(
            foia=foia,
            response=False,
            datetime=timezone.now() - timedelta(days=2),
        )
        annotated = ReviewAgencyTask.objects.with_outcome().get(pk=task.pk)
        assert not annotated.held

    def test_an_unresolved_task_is_not_held(self):
        """Nothing to have held yet"""
        task = ReviewAgencyTaskFactory(
            agency=self.agency, source="email", email=self.address, resolved=False
        )
        annotated = ReviewAgencyTask.objects.with_outcome().get(pk=task.pk)
        assert not annotated.held


class TestReopenLinkage(ResolvedReadoutMixin, TestCase):
    """A resolve that did not hold is a signal"""

    def test_a_new_task_on_the_same_channel_links_forward(self):
        """The resolved task points at the task that reopened"""
        resolved = self.resolved_task()
        successor = ReviewAgencyTaskFactory(
            agency=self.agency, source="email", email=self.address, resolved=False
        )
        assert resolved.successor == successor

    def test_a_task_on_a_different_channel_is_not_a_successor(self):
        """Each channel stands alone"""
        resolved = self.resolved_task()
        other = EmailAddressFactory(email="other@agency.gov", status="error")
        ReviewAgencyTaskFactory(
            agency=self.agency, source="email", email=other, resolved=False
        )
        assert resolved.successor is None

    def test_a_task_at_a_different_agency_is_not_a_successor(self):
        """Sameness of address does not mean sameness of workflow"""
        resolved = self.resolved_task()
        ReviewAgencyTaskFactory(
            agency=AgencyFactory(email=None, fax=None),
            source="email",
            email=self.address,
            resolved=False,
        )
        assert resolved.successor is None

    def test_no_successor_when_nothing_reopened(self):
        """The repair held, so there is nothing to link to"""
        assert self.resolved_task().successor is None

    def test_an_unresolved_task_has_no_successor(self):
        """Only a resolved task can have reopened"""
        task = ReviewAgencyTaskFactory(
            agency=self.agency, source="email", email=self.address, resolved=False
        )
        assert task.successor is None

    def test_the_newest_open_task_wins(self):
        """Several reopens link to the most recent"""
        resolved = self.resolved_task()
        ReviewAgencyTaskFactory(
            agency=self.agency, source="email", email=self.address, resolved=False
        )
        newest = ReviewAgencyTaskFactory(
            agency=self.agency, source="email", email=self.address, resolved=False
        )
        assert resolved.successor == newest

    def test_an_agency_level_task_has_no_channel_successor(self):
        """A null channel task cannot be matched on channel"""
        task = ReviewAgencyTaskFactory(agency=self.agency, source="staff", email=None)
        task.resolve(self.user)
        ReviewAgencyTaskFactory(
            agency=self.agency, source="staff", email=None, resolved=False
        )
        assert task.successor is None
