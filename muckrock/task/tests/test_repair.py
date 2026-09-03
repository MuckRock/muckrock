# -*- coding: utf-8 -*-
"""
Tests for channel repair

Repairing several channels in one pass is not optional polish: the median
multi channel agency has only 61% of its blocked requests on its biggest
channel, and 1,979 requests sit on channels that are not their agency's
biggest.  Single channel only repair structurally cannot clear the backlog.
"""

# Django
from django.test import TestCase
from django.urls import reverse

# Standard Library
from unittest import mock

# MuckRock
from muckrock.communication.factories import EmailAddressFactory
from muckrock.communication.models import EmailAddress
from muckrock.core.factories import AgencyEmailFactory, AgencyFactory, UserFactory
from muckrock.core.test_utils import RunCommitHooksMixin
from muckrock.foia.factories import FOIARequestFactory
from muckrock.task.factories import ReviewAgencyTaskFactory
from muckrock.task.forms import ChannelRepairForm


class ChannelRepairMixin:
    """Shared setup for repair tests"""

    # pylint: disable=invalid-name
    def setUp(self):
        password = "abc"
        self.user = UserFactory(is_staff=True, password=password)
        self.agency = AgencyFactory(email=None, fax=None)
        self.url = reverse("review-agency-detail", kwargs={"pk": self.agency.pk})
        self.client.login(username=self.user.username, password=password)

    def make_channel(self, email, blocked=1, request_type="primary"):
        """A broken channel on the agency, with a task and some blocked requests"""
        address = EmailAddressFactory(email=email, status="error")
        AgencyEmailFactory(
            agency=self.agency,
            email=address,
            request_type=request_type,
            email_type="to",
        )
        foias = FOIARequestFactory.create_batch(
            blocked, agency=self.agency, email=address, status="ack"
        )
        task = ReviewAgencyTaskFactory(
            agency=self.agency, source="email", email=address, resolved=False
        )
        return address, foias, task

    def post(self, **data):
        """Submit a repair"""
        data.setdefault("repair", "true")
        return self.client.post(self.url, data)


class TestChannelRepairForm(TestCase):
    """Validation rules for the repair form"""

    def test_new_email_resolves_through_fetch(self):
        """A staffer typing mixed case lands on the existing row

        Otherwise the repair itself mints a fresh case variant of the very
        mailbox the merge command just consolidated.
        """
        existing = EmailAddress.objects.fetch("foia@agency.gov")
        form = ChannelRepairForm(data={"new_email": "FOIA@Agency.gov"})
        assert form.is_valid(), form.errors
        assert form.cleaned_data["new_email"] == existing

    def test_invalid_email_is_rejected(self):
        """A malformed address does not silently become None"""
        form = ChannelRepairForm(data={"new_email": "not-an-address"})
        assert not form.is_valid()
        assert "new_email" in form.errors

    def test_address_required_unless_snail_or_resolve(self):
        """There has to be something to do"""
        assert not ChannelRepairForm(data={}).is_valid()

    def test_snail_mail_alone_is_valid(self):
        """Falling back to snail mail needs no address"""
        form = ChannelRepairForm(data={"snail_mail": "on"})
        assert form.is_valid(), form.errors

    def test_resolve_alone_is_valid(self):
        """Resolving without a contact change, when nothing is actually broken"""
        form = ChannelRepairForm(data={"resolve": "on"})
        assert form.is_valid(), form.errors

    def test_portal_channel_rejects_an_email_replacement(self):
        """No replacement email repairs a portal address

        Seattle PD's single largest channel is a GovQA notification address.
        Picking a replacement email would be actively wrong, so the form says
        so rather than accepting the repair.
        """
        portal = EmailAddressFactory(email="seattle@mycusthelp.net", status="error")
        form = ChannelRepairForm(
            data={
                "new_email": "foia@seattle.gov",
                "channel_pks": str(portal.pk),
            }
        )
        assert not form.is_valid()
        assert "portal" in str(form.errors).lower()

    def test_ordinary_channel_accepts_a_replacement(self):
        """The majority case still works"""
        dead = EmailAddressFactory(email="old@agency.gov", status="error")
        form = ChannelRepairForm(
            data={"new_email": "new@agency.gov", "channel_pks": str(dead.pk)}
        )
        assert form.is_valid(), form.errors

    def test_channel_pks_parse_as_a_list(self):
        """Several channels arrive in one submission"""
        first = EmailAddressFactory(email="a@agency.gov")
        second = EmailAddressFactory(email="b@agency.gov")
        form = ChannelRepairForm(
            data={
                "new_email": "new@agency.gov",
                "channel_pks": "%d,%d" % (first.pk, second.pk),
            }
        )
        assert form.is_valid(), form.errors
        assert set(form.cleaned_data["channel_pks"]) == {first.pk, second.pk}


@mock.patch("muckrock.task.tasks.submit_review_update.delay")
class TestSingleChannelRepair(ChannelRepairMixin, RunCommitHooksMixin, TestCase):
    """Repairing one channel"""

    def test_requests_are_repointed(self, _mock_delay):
        """The selected requests move to the new address"""
        _address, foias, _task = self.make_channel("old@agency.gov", blocked=2)
        response = self.post(
            new_email="new@agency.gov",
            foia_pks=",".join(str(f.pk) for f in foias),
        )
        assert response.status_code in (200, 302)
        new_address = EmailAddress.objects.get(email="new@agency.gov")
        for foia in foias:
            foia.refresh_from_db()
            assert foia.email == new_address

    def test_update_agency_info_promotes_and_demotes(self, _mock_delay):
        """The new address becomes primary and the old one stops being it"""
        address, foias, _task = self.make_channel("old@agency.gov", blocked=1)
        self.post(
            new_email="new@agency.gov",
            foia_pks=str(foias[0].pk),
            update_agency_info="on",
        )
        new_address = EmailAddress.objects.get(email="new@agency.gov")
        primary = self.agency.agencyemail_set.filter(
            request_type="primary", email_type="to"
        )
        assert [link.email for link in primary] == [new_address]
        old_link = self.agency.agencyemail_set.get(email=address)
        assert old_link.request_type == "none"

    def test_resolve_closes_the_task(self, _mock_delay):
        """The task resolves when asked"""
        _address, foias, task = self.make_channel("old@agency.gov", blocked=1)
        self.post(
            new_email="new@agency.gov",
            foia_pks=str(foias[0].pk),
            resolve="on",
        )
        task.refresh_from_db()
        assert task.resolved
        assert task.resolved_by == self.user

    def test_repair_without_resolve_leaves_the_task_open(self, _mock_delay):
        """Repairing is not the same as resolving"""
        _address, foias, task = self.make_channel("old@agency.gov", blocked=1)
        self.post(new_email="new@agency.gov", foia_pks=str(foias[0].pk))
        task.refresh_from_db()
        assert not task.resolved

    def test_resolve_without_a_contact_change(self, _mock_delay):
        """For cases where nothing is actually broken"""
        address, _foias, task = self.make_channel("fine@agency.gov", blocked=1)
        self.post(resolve="on", channel_pks=str(address.pk))
        task.refresh_from_db()
        assert task.resolved
        address.refresh_from_db()
        # no contact edit was recorded
        assert self.agency.agencyemail_set.get(email=address).request_type == "primary"

    def test_follow_up_is_sent_on_commit(self, mock_delay):
        """The follow up routes through the celery task after commit"""
        _address, foias, _task = self.make_channel("old@agency.gov", blocked=1)
        self.post(
            new_email="new@agency.gov",
            foia_pks=str(foias[0].pk),
            reply="Please confirm receipt.",
        )
        self.run_commit_hooks()
        mock_delay.assert_called_once()
        args = mock_delay.call_args[0]
        assert [str(foias[0].pk)] == [str(pk) for pk in args[0]]
        assert args[1] == "Please confirm receipt."

    def test_no_follow_up_when_reply_is_blank(self, mock_delay):
        """Leaving the reply blank sends nothing"""
        _address, foias, _task = self.make_channel("old@agency.gov", blocked=1)
        self.post(new_email="new@agency.gov", foia_pks=str(foias[0].pk))
        self.run_commit_hooks()
        mock_delay.assert_not_called()


@mock.patch("muckrock.task.tasks.submit_review_update.delay")
class TestMultiChannelRepair(ChannelRepairMixin, RunCommitHooksMixin, TestCase):
    """Repairing several channels in one submit"""

    def test_one_address_applied_across_three_channels(self, _mock_delay):
        """Requests drawn from three channels all move, and all tasks resolve"""
        first, first_foias, first_task = self.make_channel(
            "one@agency.gov", blocked=2, request_type="primary"
        )
        second, second_foias, second_task = self.make_channel(
            "two@agency.gov", blocked=3, request_type="none"
        )
        third, third_foias, third_task = self.make_channel(
            "three@agency.gov", blocked=1, request_type="none"
        )
        all_foias = first_foias + second_foias + third_foias

        self.post(
            new_email="new@agency.gov",
            channel_pks="%d,%d,%d" % (first.pk, second.pk, third.pk),
            foia_pks=",".join(str(f.pk) for f in all_foias),
            resolve="on",
        )

        new_address = EmailAddress.objects.get(email="new@agency.gov")
        for foia in all_foias:
            foia.refresh_from_db()
            assert foia.email == new_address
        for task in (first_task, second_task, third_task):
            task.refresh_from_db()
            assert task.resolved, "task on %s did not resolve" % task.email

    def test_only_the_submitted_channels_resolve(self, _mock_delay):
        """An untouched channel's task stays open"""
        first, first_foias, first_task = self.make_channel("one@agency.gov", blocked=1)
        _second, _second_foias, second_task = self.make_channel(
            "two@agency.gov", blocked=1, request_type="none"
        )
        self.post(
            new_email="new@agency.gov",
            channel_pks=str(first.pk),
            foia_pks=str(first_foias[0].pk),
            resolve="on",
        )
        first_task.refresh_from_db()
        second_task.refresh_from_db()
        assert first_task.resolved
        assert not second_task.resolved

    def test_portal_channel_in_the_selection_blocks_the_whole_repair(self, _mock_delay):
        """A portal channel is not quietly skipped, it stops the submission

        Quietly skipping it would leave a staffer believing the agency was
        repaired when its biggest channel was untouched.
        """
        portal, portal_foias, portal_task = self.make_channel(
            "seattle@mycusthelp.net", blocked=3
        )
        self.post(
            new_email="foia@seattle.gov",
            channel_pks=str(portal.pk),
            foia_pks=",".join(str(f.pk) for f in portal_foias),
            resolve="on",
        )
        portal_task.refresh_from_db()
        assert not portal_task.resolved
        for foia in portal_foias:
            foia.refresh_from_db()
            assert foia.email == portal


@mock.patch("muckrock.task.tasks.submit_review_update.delay")
class TestRepairOutcome(ChannelRepairMixin, RunCommitHooksMixin, TestCase):
    """What was done has to be recoverable afterward"""

    def test_outcome_is_recorded_on_the_task(self, _mock_delay):
        """Which channel, old to new, how many requests, follow up, by whom"""
        address, foias, task = self.make_channel("old@agency.gov", blocked=2)
        self.post(
            new_email="new@agency.gov",
            channel_pks=str(address.pk),
            foia_pks=",".join(str(f.pk) for f in foias),
            resolve="on",
            reply="Following up.",
        )
        task.refresh_from_db()
        outcome = task.repair_outcome
        assert outcome["old_email"] == "old@agency.gov"
        assert outcome["new_email"] == "new@agency.gov"
        assert outcome["requests_updated"] == 2
        assert outcome["followup_sent"] is True
        assert outcome["by"] == self.user.username
        assert outcome["at"]

    def test_outcome_records_a_resolve_with_no_change(self, _mock_delay):
        """Resolving without a contact edit says so"""
        address, _foias, task = self.make_channel("fine@agency.gov", blocked=1)
        self.post(resolve="on", channel_pks=str(address.pk))
        task.refresh_from_db()
        outcome = task.repair_outcome
        assert outcome["new_email"] is None
        assert outcome["requests_updated"] == 0

    def test_no_outcome_on_an_untouched_task(self, _mock_delay):
        """A task nobody acted on has nothing to report"""
        _address, _foias, task = self.make_channel("old@agency.gov", blocked=1)
        assert task.repair_outcome is None
