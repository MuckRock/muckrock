# -*- coding: utf-8 -*-
"""
Tests for channel repair

Repairing several channels in one pass is not optional polish: the median
multi channel agency has only 61% of its blocked requests on its biggest
channel, and 1,979 requests sit on channels that are not their agency's
biggest.  Single channel only repair structurally cannot clear the backlog.
"""

# Django
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

# Standard Library
from datetime import timedelta
from unittest import mock

# MuckRock
from muckrock.communication.factories import EmailAddressFactory, PhoneNumberFactory
from muckrock.communication.models import EmailAddress
from muckrock.core.factories import (
    AgencyEmailFactory,
    AgencyFactory,
    AgencyPhoneFactory,
    UserFactory,
)
from muckrock.core.test_utils import RunCommitHooksMixin
from muckrock.foia.factories import FOIACommunicationFactory, FOIARequestFactory
from muckrock.foia.models import FOIACommunication, FOIARequest
from muckrock.portal.models import Portal
from muckrock.task.factories import ReviewAgencyTaskFactory
from muckrock.task.forms import ChannelRepairForm
from muckrock.task.models import PortalTask
from muckrock.task.tasks import submit_review_update


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

    def test_portal_address_rejected_as_the_replacement(self):
        """Moving requests onto a portal notification address strands them

        Mail to a GovQA or NextRequest sender never reaches the records
        office.  Found in local testing: Seattle PD's healthy channels were
        "repaired" onto its own seattle@mycusthelp.net notification address.
        """
        healthy = EmailAddressFactory(email="spdpdr@seattle.gov", status="error")
        form = ChannelRepairForm(
            data={
                "new_email": "seattle@mycusthelp.net",
                "channel_pks": str(healthy.pk),
                "resolve": "on",
            }
        )
        assert not form.is_valid()
        assert "portal" in str(form.errors["new_email"])

    def test_portal_replacement_rejected_without_a_channel_selection(self):
        """Requests picked individually are stranded just the same"""
        form = ChannelRepairForm(data={"new_email": "agency@govqa.us"})
        assert not form.is_valid()
        assert "new_email" in form.errors

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

    def test_update_agency_info_promotes_an_existing_link(self, _mock_delay):
        """An address already on file is promoted, not linked a second time"""
        address, foias, _task = self.make_channel("old@agency.gov", blocked=1)
        existing = EmailAddressFactory(email="new@agency.gov")
        AgencyEmailFactory(
            agency=self.agency, email=existing, request_type="none", email_type="none"
        )
        self.post(
            new_email="new@agency.gov",
            foia_pks=str(foias[0].pk),
            update_agency_info="on",
        )
        links = self.agency.agencyemail_set.filter(email=existing)
        assert links.count() == 1
        assert (links.get().request_type, links.get().email_type) == (
            "primary",
            "to",
        )
        assert self.agency.agencyemail_set.get(email=address).request_type == "none"

    def test_update_agency_info_promotes_an_existing_fax(self, _mock_delay):
        """Faxes follow the same rule as email"""
        _address, foias, task = self.make_channel("old@agency.gov", blocked=1)
        fax = PhoneNumberFactory(type="fax")
        AgencyPhoneFactory(agency=self.agency, phone=fax, request_type="none")
        task.update_contact(fax, foias, True, False)
        links = self.agency.agencyphone_set.filter(phone=fax)
        assert links.count() == 1
        assert links.get().request_type == "primary"

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

    def test_no_follow_up_without_a_contact_change(self, mock_delay):
        """Resolving without a new address must not mail the broken one again

        The follow up would go to the same dead mailbox and bounce, reopening
        the very task being resolved.
        """
        address, foias, task = self.make_channel("old@agency.gov", blocked=1)
        self.post(
            channel_pks=str(address.pk),
            foia_pks=str(foias[0].pk),
            reply="Please confirm receipt.",
            resolve="on",
        )
        self.run_commit_hooks()
        mock_delay.assert_not_called()
        task.refresh_from_db()
        assert task.repair_outcome["followup_sent"] is False

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

    def test_agency_level_task_resolves_with_any_channel(self, _mock_delay):
        """A task with no channel covers them all, so a repair includes it

        Most legacy tasks are agency level; matching only on the selected
        channels left them open with nothing blocked.
        """
        address = EmailAddressFactory(email="old@agency.gov", status="error")
        AgencyEmailFactory(agency=self.agency, email=address)
        foias = FOIARequestFactory.create_batch(
            2, agency=self.agency, email=address, status="ack"
        )
        task = ReviewAgencyTaskFactory(agency=self.agency, email=None, resolved=False)
        self.post(
            new_email="new@agency.gov",
            channel_pks=str(address.pk),
            foia_pks=",".join(str(f.pk) for f in foias),
            resolve="on",
        )
        task.refresh_from_db()
        assert task.resolved
        assert task.repair_outcome["requests_updated"] == 2

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

    def test_each_task_records_its_own_request_count(self, _mock_delay):
        """One submit across channels: each outcome counts its own channel

        Recording the submission total on every task made a channel that held
        one request read as having had five moved off it.
        """
        first, first_foias, first_task = self.make_channel("one@agency.gov", 4)
        second, second_foias, second_task = self.make_channel(
            "two@agency.gov", 1, request_type="none"
        )
        self.post(
            new_email="new@agency.gov",
            channel_pks="%d,%d" % (first.pk, second.pk),
            foia_pks=",".join(str(f.pk) for f in first_foias + second_foias),
            resolve="on",
        )
        first_task.refresh_from_db()
        second_task.refresh_from_db()
        assert first_task.repair_outcome["requests_updated"] == 4
        assert second_task.repair_outcome["requests_updated"] == 1

    def test_agency_level_task_counts_requests_without_a_task(self, _mock_delay):
        """The agency level task covers channels that have no task of their own"""
        covered, covered_foias, covered_task = self.make_channel("one@agency.gov", 2)
        loose = EmailAddressFactory(email="loose@agency.gov", status="error")
        loose_foias = FOIARequestFactory.create_batch(
            3, agency=self.agency, email=loose, status="ack"
        )
        agency_task = ReviewAgencyTaskFactory(
            agency=self.agency, source="email", email=None, resolved=False
        )
        self.post(
            new_email="new@agency.gov",
            channel_pks="%d,%d" % (covered.pk, loose.pk),
            foia_pks=",".join(str(f.pk) for f in covered_foias + loose_foias),
            resolve="on",
        )
        covered_task.refresh_from_db()
        agency_task.refresh_from_db()
        assert covered_task.repair_outcome["requests_updated"] == 2
        assert agency_task.repair_outcome["requests_updated"] == 3

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


@mock.patch("muckrock.task.tasks.submit_review_update.delay")
class TestRepairResponse(ChannelRepairMixin, RunCommitHooksMixin, TestCase):
    """Where a repair lands the staffer, and what it tells them"""

    def test_redirects_to_the_queue_filtered_to_the_agency(self, _mock_delay):
        """The queue shows the agency's new blocked total, so it can be resolved"""
        address, foias, _task = self.make_channel("old@agency.gov", blocked=1)
        response = self.post(
            new_email="new@agency.gov",
            channel_pks=str(address.pk),
            foia_pks=str(foias[0].pk),
        )
        self.assertRedirects(
            response,
            "%s?agency=%d" % (reverse("review-agency-task-list"), self.agency.pk),
            fetch_redirect_response=False,
        )

    def test_redirects_to_the_whole_queue_once_nothing_is_left(self, _mock_delay):
        """A filtered queue with every task resolved would be empty"""
        address, foias, _task = self.make_channel("old@agency.gov", blocked=1)
        response = self.post(
            new_email="new@agency.gov",
            channel_pks=str(address.pk),
            foia_pks=str(foias[0].pk),
            resolve="on",
        )
        self.assertRedirects(
            response,
            reverse("review-agency-task-list"),
            fetch_redirect_response=False,
        )

    def test_stays_filtered_while_the_agency_has_open_tasks(self, _mock_delay):
        """Resolving one channel's task leaves the others to work through"""
        first, first_foias, _first_task = self.make_channel("one@agency.gov")
        self.make_channel("two@agency.gov", request_type="none")
        response = self.post(
            new_email="new@agency.gov",
            channel_pks=str(first.pk),
            foia_pks=str(first_foias[0].pk),
            resolve="on",
        )
        self.assertRedirects(
            response,
            "%s?agency=%d" % (reverse("review-agency-task-list"), self.agency.pk),
            fetch_redirect_response=False,
        )

    def test_message_counts_the_rerouted_requests(self, _mock_delay):
        """Counted from the requests moved, not from the tasks matched

        A channel can have blocked requests without a task of its own -- the
        agency level task covers it -- and the message still has to say what
        moved.
        """
        address = EmailAddressFactory(email="old@agency.gov", status="error")
        AgencyEmailFactory(agency=self.agency, email=address)
        foias = FOIARequestFactory.create_batch(
            3, agency=self.agency, email=address, status="ack"
        )
        ReviewAgencyTaskFactory(agency=self.agency, email=None, resolved=False)
        response = self.post(
            new_email="new@agency.gov",
            channel_pks=str(address.pk),
            foia_pks=",".join(str(f.pk) for f in foias),
        )
        message = str(list(get_messages(response.wsgi_request))[0])
        assert "Rerouted 3 requests" in message
        assert "1 channel " in message


class TestPortalRepairForm(TestCase):
    """Validation rules for moving requests to a portal"""

    def setUp(self):
        self.agency = AgencyFactory(email=None, fax=None)
        self.foia = FOIARequestFactory(agency=self.agency)

    def form(self, **data):
        """A portal mode form for the agency"""
        data.setdefault("repair_via", "portal")
        data.setdefault("foia_pks", str(self.foia.pk))
        return ChannelRepairForm(data=data, agency=self.agency)

    def test_uses_the_agency_portal(self):
        """An agency with a working portal needs nothing else filled in"""
        self.agency.portal = Portal.objects.create(
            url="https://seattle.govqa.us", name="Seattle GovQA", type="govqa"
        )
        self.agency.save()
        form = self.form()
        assert form.is_valid(), form.errors
        assert form.cleaned_data["portal"] == self.agency.portal

    def test_portal_channels_are_welcome(self):
        """The portal notification address is exactly what this repair is for"""
        self.agency.portal = Portal.objects.create(
            url="https://seattle.govqa.us", name="Seattle GovQA", type="govqa"
        )
        self.agency.save()
        channel = EmailAddressFactory(email="seattle@mycusthelp.net", status="error")
        form = self.form(channel_pks=str(channel.pk))
        assert form.is_valid(), form.errors

    def test_a_broken_portal_stops_the_repair(self):
        """A portal marked Error points at a bigger problem than routing"""
        self.agency.portal = Portal.objects.create(
            url="https://seattle.govqa.us",
            name="Seattle GovQA",
            type="govqa",
            status="error",
        )
        self.agency.save()
        form = self.form()
        assert not form.is_valid()
        assert "error" in str(form.errors).lower()

    def test_a_new_portal_needs_its_details(self):
        """With no portal on the agency, one has to be described"""
        form = self.form()
        assert not form.is_valid()
        assert "portal_url" in form.errors
        assert "portal_type" in form.errors

    def test_a_new_portal_is_built_but_not_saved(self):
        """Saving waits for the repair's transaction"""
        form = self.form(
            portal_url="https://seattle.govqa.us",
            portal_name="Seattle GovQA",
            portal_type="govqa",
        )
        assert form.is_valid(), form.errors
        portal = form.cleaned_data["portal"]
        assert portal.pk is None
        assert portal.url == "https://seattle.govqa.us"
        assert portal.type == "govqa"

    def test_a_known_portal_url_is_reused(self):
        """Portal URLs are unique, so a match is the same portal"""
        existing = Portal.objects.create(
            url="https://seattle.govqa.us", name="Seattle GovQA", type="govqa"
        )
        form = self.form(
            portal_url="https://Seattle.GovQA.us",
            portal_name="Anything",
            portal_type="nextrequest",
        )
        assert form.is_valid(), form.errors
        assert form.cleaned_data["portal"] == existing

    def test_a_known_broken_portal_is_not_reused(self):
        """Matching a broken portal by URL bails out like the agency's own"""
        Portal.objects.create(
            url="https://seattle.govqa.us",
            name="Seattle GovQA",
            type="govqa",
            status="error",
        )
        form = self.form(
            portal_url="https://seattle.govqa.us",
            portal_name="Seattle GovQA",
            portal_type="govqa",
        )
        assert not form.is_valid()

    def test_foiaonline_is_not_offered(self):
        """FOIAonline is discontinued"""
        form = self.form(
            portal_url="https://foiaonline.gov",
            portal_name="FOIAonline",
            portal_type="foiaonline",
        )
        assert not form.is_valid()
        assert "portal_type" in form.errors

    def test_needs_requests_to_move(self):
        """A portal repair is per request; with none selected there is nothing"""
        self.agency.portal = Portal.objects.create(
            url="https://seattle.govqa.us", name="Seattle GovQA", type="govqa"
        )
        self.agency.save()
        form = self.form(foia_pks="")
        assert not form.is_valid()

    def test_no_replacement_email_is_required(self):
        """The email rule belongs to email repairs"""
        self.agency.portal = Portal.objects.create(
            url="https://seattle.govqa.us", name="Seattle GovQA", type="govqa"
        )
        self.agency.save()
        form = self.form()
        assert form.is_valid(), form.errors
        assert "new_email" not in form.errors


@mock.patch("muckrock.task.tasks.submit_review_update.delay")
class TestPortalRepair(ChannelRepairMixin, RunCommitHooksMixin, TestCase):
    """Moving requests off a broken email channel into a portal

    Each request is resent through the portal by hand, so each gets its own
    Portal Task -- the same thing resending one request at a time does.
    """

    def make_portal_channel(self, blocked=2):
        """A broken portal notification channel whose requests were filed"""
        address, foias, task = self.make_channel(
            "seattle@mycusthelp.net", blocked=blocked
        )
        comms = [
            FOIACommunicationFactory(foia=foia, category="n", response=False)
            for foia in foias
        ]
        return address, foias, comms, task

    def test_each_request_gets_its_own_portal_task(self, _mock_delay):
        """One Portal Task per request, on its initial communication"""
        self.agency.portal = Portal.objects.create(
            url="https://seattle.govqa.us", name="Seattle GovQA", type="govqa"
        )
        self.agency.save()
        address, foias, comms, _task = self.make_portal_channel(blocked=3)
        self.post(
            repair_via="portal",
            channel_pks=str(address.pk),
            foia_pks=",".join(str(f.pk) for f in foias),
        )
        tasks = PortalTask.objects.filter(resolved=False)
        assert sorted(t.communication_id for t in tasks) == sorted(c.pk for c in comms)
        assert {t.category for t in tasks} == {"n"}
        for foia in foias:
            foia.refresh_from_db()
            assert foia.portal == self.agency.portal
            assert foia.status == "submitted"

    def test_a_new_portal_is_attached_to_the_agency(self, _mock_delay):
        """Creating the portal is part of the repair"""
        address, foias, _comms, _task = self.make_portal_channel(blocked=1)
        self.post(
            repair_via="portal",
            channel_pks=str(address.pk),
            foia_pks=str(foias[0].pk),
            portal_url="https://seattle.govqa.us",
            portal_name="Seattle GovQA",
            portal_type="govqa",
        )
        portal = Portal.objects.get(url="https://seattle.govqa.us")
        self.agency.refresh_from_db()
        assert self.agency.portal == portal
        assert PortalTask.objects.filter(communication__foia=foias[0]).count() == 1

    def test_only_selected_requests_move(self, _mock_delay):
        """A deselected request stays where it is"""
        self.agency.portal = Portal.objects.create(
            url="https://seattle.govqa.us", name="Seattle GovQA", type="govqa"
        )
        self.agency.save()
        address, foias, _comms, _task = self.make_portal_channel(blocked=2)
        self.post(
            repair_via="portal",
            channel_pks=str(address.pk),
            foia_pks=str(foias[0].pk),
        )
        foias[1].refresh_from_db()
        assert foias[1].portal is None
        assert not PortalTask.objects.filter(communication__foia=foias[1]).exists()

    def test_no_follow_up_is_sent(self, mock_delay):
        """A follow-up would go through the portal too -- a second task each"""
        self.agency.portal = Portal.objects.create(
            url="https://seattle.govqa.us", name="Seattle GovQA", type="govqa"
        )
        self.agency.save()
        address, foias, _comms, _task = self.make_portal_channel(blocked=1)
        self.post(
            repair_via="portal",
            channel_pks=str(address.pk),
            foia_pks=str(foias[0].pk),
            reply="Please confirm receipt.",
        )
        self.run_commit_hooks()
        mock_delay.assert_not_called()

    def test_outcome_names_the_portal(self, _mock_delay):
        """The readout says the channel moved to a portal"""
        self.agency.portal = Portal.objects.create(
            url="https://seattle.govqa.us", name="Seattle GovQA", type="govqa"
        )
        self.agency.save()
        address, foias, _comms, task = self.make_portal_channel(blocked=2)
        self.post(
            repair_via="portal",
            channel_pks=str(address.pk),
            foia_pks=",".join(str(f.pk) for f in foias),
            reply="Ignored.",
            resolve="on",
        )
        task.refresh_from_db()
        assert task.resolved
        outcome = task.repair_outcome
        assert outcome["portal"] == "Seattle GovQA"
        assert outcome["new_email"] is None
        assert outcome["requests_updated"] == 2
        assert outcome["followup_sent"] is False

    def test_agency_level_task_resolves_after_moving_everything(self, _mock_delay):
        """Requests resubmitted through the portal are no longer blocked"""
        self.agency.portal = Portal.objects.create(
            url="https://seattle.govqa.us", name="Seattle GovQA", type="govqa"
        )
        self.agency.save()
        address, foias, _comms, _task = self.make_portal_channel(blocked=2)
        agency_task = ReviewAgencyTaskFactory(
            agency=self.agency, email=None, resolved=False
        )
        self.post(
            repair_via="portal",
            channel_pks=str(address.pk),
            foia_pks=",".join(str(f.pk) for f in foias),
            resolve="on",
        )
        agency_task.refresh_from_db()
        assert agency_task.resolved

    def test_resends_the_first_outgoing_communication(self, _mock_delay):
        """An agency reply that happens to come first is not the request"""
        self.agency.portal = Portal.objects.create(
            url="https://seattle.govqa.us", name="Seattle GovQA", type="govqa"
        )
        self.agency.save()
        address, foias, _task = self.make_channel("seattle@mycusthelp.net")
        foia = foias[0]
        FOIACommunicationFactory(
            foia=foia, response=True, datetime=timezone.now() - timedelta(days=2)
        )
        request = FOIACommunicationFactory(
            foia=foia,
            response=False,
            category="n",
            datetime=timezone.now() - timedelta(days=1),
        )
        self.post(
            repair_via="portal", channel_pks=str(address.pk), foia_pks=str(foia.pk)
        )
        assert [t.communication for t in PortalTask.objects.all()] == [request]

    def test_a_request_with_nothing_to_resend_is_skipped(self, _mock_delay):
        """One request with no outgoing communication does not sink the repair

        It stays on its channel, still blocked, and the staffer is told.
        """
        self.agency.portal = Portal.objects.create(
            url="https://seattle.govqa.us", name="Seattle GovQA", type="govqa"
        )
        self.agency.save()
        address, foias, _comms, task = self.make_portal_channel(blocked=1)
        empty = FOIARequestFactory(agency=self.agency, email=address, status="ack")
        response = self.post(
            repair_via="portal",
            channel_pks=str(address.pk),
            foia_pks="%d,%d" % (foias[0].pk, empty.pk),
        )
        foias[0].refresh_from_db()
        empty.refresh_from_db()
        assert foias[0].portal == self.agency.portal
        assert empty.portal is None
        assert empty.email == address
        assert empty.status == "ack"
        task.refresh_from_db()
        assert task.repair_outcome["requests_updated"] == 1
        message = str(list(get_messages(response.wsgi_request))[0])
        assert "Rerouted 1 request" in message
        assert "Skipped 1 request with no filed request to resend" in message

    def test_message_counts_the_portal_tasks(self, _mock_delay):
        """The staffer is told how much portal work was just queued"""
        self.agency.portal = Portal.objects.create(
            url="https://seattle.govqa.us", name="Seattle GovQA", type="govqa"
        )
        self.agency.save()
        address, foias, _comms, _task = self.make_portal_channel(blocked=2)
        response = self.post(
            repair_via="portal",
            channel_pks=str(address.pk),
            foia_pks=",".join(str(f.pk) for f in foias),
        )
        message = str(list(get_messages(response.wsgi_request))[0])
        assert "2 Portal Tasks" in message

    def test_a_broken_portal_changes_nothing(self, _mock_delay):
        """Bailing out leaves the requests and task as they were"""
        self.agency.portal = Portal.objects.create(
            url="https://seattle.govqa.us",
            name="Seattle GovQA",
            type="govqa",
            status="error",
        )
        self.agency.save()
        address, foias, _comms, task = self.make_portal_channel(blocked=1)
        self.post(
            repair_via="portal",
            channel_pks=str(address.pk),
            foia_pks=str(foias[0].pk),
        )
        task.refresh_from_db()
        assert not task.resolved
        assert not PortalTask.objects.exists()


class TestSubmitReviewUpdate(TestCase):
    """The follow up job after a repair"""

    def setUp(self):
        UserFactory(username="MuckrockStaff")
        self.foias = FOIARequestFactory.create_batch(3, status="ack")
        self.pks = [foia.pk for foia in self.foias]

    def test_one_failing_request_does_not_stop_the_rest(self):
        """Every request gets its follow up even if one of them fails

        A missing law record once crashed the job on its first request, so
        the follow ups for every other request were silently never sent.
        """
        failing = self.pks[0]

        def submit(foia, **kwargs):
            # pylint: disable=unused-argument
            if foia.pk == failing:
                raise ValueError("broken request")

        with mock.patch.object(
            FOIARequest, "submit", autospec=True, side_effect=submit
        ) as mock_submit:
            submit_review_update(self.pks, "Following up.")
        assert mock_submit.call_count == 3
        followups = FOIACommunication.objects.filter(
            communication="Following up."
        ).values_list("foia_id", flat=True)
        # the failed request's follow up is rolled back rather than left
        # looking sent
        assert sorted(followups) == sorted(self.pks[1:])
