# -*- coding: utf-8 -*-
"""
Tests for the review agency repair history

A resolved task used to show the agency as it is now, not what was done to it:
the errored address dropped off the task once its requests were moved, and the
follow ups the repair sent were nowhere to be found (#1869, #1870).  Each repair
is now recorded with what the channels looked like before it ran, and with the
communications it sent.
"""

# Django
from django.apps import apps as django_apps
from django.core.management import call_command
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

# Standard Library
from datetime import timedelta
from importlib import import_module
from unittest import mock

# MuckRock
from muckrock.communication.factories import EmailAddressFactory
from muckrock.communication.models import EmailAddress
from muckrock.core.factories import AgencyFactory, UserFactory
from muckrock.core.test_utils import RunCommitHooksMixin
from muckrock.foia.factories import FOIACommunicationFactory, FOIARequestFactory
from muckrock.foia.models import FOIACommunication, FOIARequest
from muckrock.portal.models import Portal
from muckrock.task.factories import ReviewAgencyTaskFactory
from muckrock.task.models import ReviewAgencyRepair, ReviewAgencyTask
from muckrock.task.tasks import submit_review_update
from muckrock.task.tests.test_channels import add_error
from muckrock.task.tests.test_repair import ChannelRepairMixin


@mock.patch("muckrock.task.tasks.submit_review_update.delay")
class TestRepairRecord(ChannelRepairMixin, RunCommitHooksMixin, TestCase):
    """Each repair submission is recorded once"""

    def test_one_record_covers_every_task_the_repair_touched(self, _mock_delay):
        """A multi channel repair is one action, not one per task"""
        first, first_foias, first_task = self.make_channel("a@agency.gov", blocked=2)
        second, second_foias, second_task = self.make_channel("b@agency.gov")
        agency_task = ReviewAgencyTaskFactory(
            agency=self.agency, source="staff", resolved=False
        )
        self.post(
            new_email="new@agency.gov",
            channel_pks="%d,%d" % (first.pk, second.pk),
            foia_pks=",".join(str(f.pk) for f in first_foias + second_foias),
            update_agency_info="on",
            resolve="on",
            reply="Please confirm receipt.",
        )

        repair = ReviewAgencyRepair.objects.get()
        assert repair.agency == self.agency
        assert repair.user == self.user
        assert repair.new_email.email == "new@agency.gov"
        assert repair.agency_info_updated is True
        assert repair.snail_mail is False
        assert repair.followup_sent is True
        assert repair.reply == "Please confirm receipt."
        assert repair.requests_updated == 3
        assert set(repair.tasks.all()) == {first_task, second_task, agency_task}

    def test_the_channels_are_snapshotted_before_the_repair(self, _mock_delay):
        """How each channel was broken, read before the repair changed anything"""
        address, foias, _task = self.make_channel("old@agency.gov", blocked=2)
        add_error(address, code="550", days_ago=3)
        self.post(
            new_email="new@agency.gov",
            channel_pks=str(address.pk),
            foia_pks=",".join(str(f.pk) for f in foias),
            update_agency_info="on",
            resolve="on",
        )

        repair = ReviewAgencyRepair.objects.get()
        (channel,) = repair.before["channels"]
        assert channel["email"] == "old@agency.gov"
        assert channel["status"] == "error"
        assert channel["is_primary"] is True
        assert channel["last_error_code"] == "550"
        assert channel["last_error_message"] == "Mailbox does not exist (SMTP 550)"
        assert channel["error_count"] == 1
        assert channel["requests_moved"] == 2
        assert channel["last_error"]
        # Primary before the update demoted it
        assert repair.before["primary_emails"] == ["old@agency.gov"]

    def test_follow_up_text_is_kept_only_when_sent(self, mock_delay):
        """A reply that was never sent must not read as if it went out"""
        address, foias, _task = self.make_channel("old@agency.gov")
        self.post(
            channel_pks=str(address.pk),
            foia_pks=str(foias[0].pk),
            reply="Please confirm receipt.",
            resolve="on",
        )
        self.run_commit_hooks()
        mock_delay.assert_not_called()
        repair = ReviewAgencyRepair.objects.get()
        assert repair.followup_sent is False
        assert repair.reply == ""

    def test_follow_up_job_is_told_which_repair_it_belongs_to(self, mock_delay):
        """So the job can link the communications it creates"""
        _address, foias, _task = self.make_channel("old@agency.gov")
        self.post(
            new_email="new@agency.gov",
            foia_pks=str(foias[0].pk),
            reply="Please confirm receipt.",
        )
        self.run_commit_hooks()
        repair = ReviewAgencyRepair.objects.get()
        assert mock_delay.call_args.kwargs["repair_pk"] == repair.pk


@mock.patch("muckrock.task.tasks.submit_review_update.delay")
class TestPortalRepairRecord(ChannelRepairMixin, RunCommitHooksMixin, TestCase):
    """A move to a portal is recorded as one, not as no contact change"""

    def setUp(self):
        super().setUp()
        self.agency.portal = Portal.objects.create(
            url="https://seattle.govqa.us", name="Seattle GovQA", type="govqa"
        )
        self.agency.save()

    def move(self, blocked=2, unsent=0):
        """Move a channel's requests to the portal, `unsent` with nothing to resend"""
        address, foias, task = self.make_channel(
            "seattle@mycusthelp.net", blocked=blocked + unsent
        )
        comms = [
            FOIACommunicationFactory(foia=foia, category="n", response=False)
            for foia in foias[:blocked]
        ]
        self.post(
            repair_via="portal",
            channel_pks=str(address.pk),
            foia_pks=",".join(str(f.pk) for f in foias),
            resolve="on",
        )
        return comms, task

    def test_the_portal_is_recorded(self, _mock_delay):
        """Where the requests went, and that nothing was sent by email"""
        comms, _task = self.move()
        repair = ReviewAgencyRepair.objects.get()
        assert repair.portal == self.agency.portal
        assert repair.new_email is None
        assert repair.followup_sent is False
        assert repair.requests_updated == 2
        assert set(repair.communications.all()) == set(comms)

    def test_skipped_requests_are_not_counted_as_moved(self, _mock_delay):
        """A request with nothing to resend stays on its channel"""
        comms, _task = self.move(blocked=1, unsent=1)
        repair = ReviewAgencyRepair.objects.get()
        assert repair.requests_updated == 1
        (channel,) = repair.before["channels"]
        assert channel["requests_moved"] == 1
        assert set(repair.communications.all()) == set(comms)

    def test_readout_names_the_portal(self, _mock_delay):
        """The After column says portal, not no contact change"""
        _comms, task = self.move()
        response = self.client.get(
            reverse("review-agency-task", kwargs={"pk": task.pk})
        )
        content = response.content.decode()
        start = content.index("review-agency-history")
        content = content[start:]
        assert "Seattle GovQA" in content
        assert "No contact change" not in content
        assert "resubmitted through the portal" in content


class TestFollowUpLinkage(TestCase):
    """The follow up job records what it sent"""

    def setUp(self):
        UserFactory(username="MuckrockStaff")

    def test_sent_follow_ups_are_linked_and_failures_are_not(self):
        """A rolled back follow up is not linked as if it had been sent"""
        foias = FOIARequestFactory.create_batch(3, status="ack")
        repair = ReviewAgencyRepair.objects.create(agency=foias[0].agency)
        failing = foias[0].pk

        def submit(foia, **kwargs):
            if foia.pk == failing:
                raise ValueError("broken request")

        with mock.patch.object(
            FOIARequest, "submit", autospec=True, side_effect=submit
        ):
            submit_review_update(
                [f.pk for f in foias], "Following up.", repair_pk=repair.pk
            )
        linked = sorted(repair.communications.values_list("foia_id", flat=True))
        assert linked == sorted(f.pk for f in foias[1:])
        assert all(
            comm.communication == "Following up."
            for comm in repair.communications.all()
        )

    def test_the_job_still_runs_without_a_repair(self):
        """Jobs queued by the legacy form, or before deploy, carry no repair"""
        foia = FOIARequestFactory(status="ack")
        with mock.patch.object(FOIARequest, "submit", autospec=True):
            submit_review_update([foia.pk], "Following up.")
        assert FOIACommunication.objects.filter(foia=foia).exists()


@mock.patch("muckrock.task.tasks.submit_review_update.delay")
class TestRepairHistoryReadout(ChannelRepairMixin, RunCommitHooksMixin, TestCase):
    """The resolved task shows before, after and what was sent"""

    def render(self, task):
        """The rendered readout for one task

        Just the readout: the repair's success message names the same
        addresses and would satisfy these assertions on its own.
        """
        response = self.client.get(
            reverse("review-agency-task", kwargs={"pk": task.pk})
        )
        assert response.status_code == 200
        content = response.content.decode()
        if "review-agency-outcome" not in content:
            return ""
        start = content.index("review-agency-outcome")
        return content[start : content.index("review-agency-summary", start)]

    def repair(self, address, foias, new_email, **extra):
        """Submit a resolving repair onto a new address"""
        data = {
            "new_email": new_email,
            "channel_pks": str(address.pk),
            "foia_pks": ",".join(str(f.pk) for f in foias),
            "update_agency_info": "on",
            "resolve": "on",
            "reply": "Please confirm receipt.",
        }
        data.update(extra)
        self.post(**data)

    def test_resolved_channel_task_shows_the_error_it_was_resolved_on(
        self, _mock_delay
    ):
        """The broken address and its error survive the repair

        Its requests have moved, so the live data no longer lists it -- the
        reason some resolved tasks showed the error and others did not.
        """
        address, foias, task = self.make_channel("old@agency.gov")
        add_error(address, code="550")
        self.repair(address, foias, "new@agency.gov")
        task.refresh_from_db()
        content = self.render(task)
        assert "review-agency-history" in content
        assert "old@agency.gov" in content
        assert "Mailbox does not exist (SMTP 550)" in content
        assert "new@agency.gov" in content

    def test_resolved_task_notes_the_follow_up(self, _mock_delay):
        """The readout says a follow up went out, not what it said"""
        address, foias, task = self.make_channel("old@agency.gov")
        self.repair(address, foias, "new@agency.gov")
        content = self.render(task)
        assert "follow-up sent" in content
        assert "Please confirm receipt." not in content

    def test_resolved_task_links_the_follow_ups(self, _mock_delay):
        """Each communication the repair sent is in the follow-up dropdown"""
        address, foias, task = self.make_channel("old@agency.gov")
        self.repair(address, foias, "new@agency.gov")
        UserFactory(username="MuckrockStaff")
        repair = ReviewAgencyRepair.objects.get()
        with mock.patch.object(FOIARequest, "submit", autospec=True):
            submit_review_update(
                [f.pk for f in foias], repair.reply, repair_pk=repair.pk
            )
        (comm,) = repair.communications.all()
        content = self.render(task)
        assert "review-agency-followups" in content
        assert comm.get_absolute_url() in content

    def test_agency_task_rolls_up_every_repair_on_the_agency(self, _mock_delay):
        """#1870: every address change, including those made via channel tasks"""
        agency_task = ReviewAgencyTaskFactory(
            agency=self.agency, source="staff", resolved=False
        )
        first, first_foias, _ = self.make_channel("a@agency.gov")
        # Two repairs on separate days; the agency task stays open after the
        # first because resolve is off
        self.repair(first, first_foias, "b@agency.gov", resolve="")
        second, second_foias, _ = self.make_channel("c@agency.gov")
        self.repair(second, second_foias, "d@agency.gov")

        content = self.render(agency_task)
        for email in ("a@agency.gov", "b@agency.gov", "c@agency.gov", "d@agency.gov"):
            assert email in content

    def test_agency_task_does_not_claim_repairs_from_before_it_opened(
        self, _mock_delay
    ):
        """An earlier, unrelated repair is not this task's history"""
        old, old_foias, _ = self.make_channel("ancient@agency.gov")
        self.repair(old, old_foias, "interim@agency.gov")
        ReviewAgencyRepair.objects.update(datetime=timezone.now() - timedelta(days=90))
        agency_task = ReviewAgencyTaskFactory(
            agency=self.agency, source="staff", resolved=False
        )
        assert "ancient@agency.gov" not in self.render(agency_task)

    def test_queue_cost_does_not_grow_with_repairs(self, _mock_delay):
        """Rendering the history costs the same for one repaired task or many

        Left open, so the cost measured is the history's and not the reopen
        lookup's, which resolved channel tasks make one at a time.
        """
        url = reverse("review-agency-task-list")

        def repaired_task(index):
            address, foias, _task = self.make_channel("old%d@agency.gov" % index)
            self.repair(address, foias, "new%d@agency.gov" % index, resolve="")
            # Shows and clears the success message, whose session write would
            # otherwise be counted against the next page
            self.client.get(url)

        repaired_task(0)
        with CaptureQueriesContext(connection) as one:
            self.client.get(url)
        repaired_task(1)
        repaired_task(2)
        with CaptureQueriesContext(connection) as three:
            self.client.get(url)
        assert len(three) == len(one)
        assert "new2@agency.gov" in self.client.get(url).content.decode()


class TestBackfill(TestCase):
    """Repairs recorded in form_data before the history existed"""

    def backfill(self):
        """Run the data migration's forward function"""
        migration = import_module("muckrock.task.migrations.0063_backfill_repairs")
        migration.backfill_repairs(django_apps, None)

    def recorded_task(self, agency, old_email, at, **outcome):
        """A task resolved with an old-style outcome in form_data"""
        address = EmailAddressFactory(email=old_email, status="error")
        task = ReviewAgencyTaskFactory(agency=agency, source="email", email=address)
        payload = {
            "old_email": old_email,
            "new_email": "new@agency.gov",
            "requests_updated": 2,
            "followup_sent": True,
            "agency_info_updated": True,
            "snail_mail": False,
            "by": self.user.username,
            "at": at,
        }
        payload.update(outcome)
        task.resolve(self.user, {"repair": payload})
        return task

    def setUp(self):
        self.user = UserFactory()

    def test_one_submission_across_tasks_becomes_one_repair(self):
        """Tasks sharing an agency, user and timestamp were one submission"""
        agency_task = ReviewAgencyTaskFactory(source="staff")
        agency = agency_task.agency
        at = timezone.now().isoformat()
        EmailAddressFactory(email="new@agency.gov")
        first = self.recorded_task(agency, "a@agency.gov", at)
        second = self.recorded_task(agency, "b@agency.gov", at, requests_updated=1)
        agency_task.resolve(
            self.user,
            {
                "repair": dict(
                    first.form_data["repair"], old_email=None, requests_updated=0
                )
            },
        )
        later = self.recorded_task(
            agency, "c@agency.gov", (timezone.now() + timedelta(hours=1)).isoformat()
        )

        self.backfill()

        assert ReviewAgencyRepair.objects.count() == 2
        repair = ReviewAgencyRepair.objects.get(tasks=first)
        assert set(repair.tasks.all()) == {first, second, agency_task}
        assert repair.user == self.user
        assert repair.new_email.email == "new@agency.gov"
        assert repair.requests_updated == 3
        assert repair.before["backfilled"] is True
        assert sorted(c["email"] for c in repair.before["channels"]) == [
            "a@agency.gov",
            "b@agency.gov",
        ]
        assert ReviewAgencyRepair.objects.get(tasks=later) != repair

    def test_backfill_is_idempotent(self):
        """Running it twice does not duplicate history"""
        agency_task = ReviewAgencyTaskFactory(source="staff")
        self.recorded_task(
            agency_task.agency, "a@agency.gov", timezone.now().isoformat()
        )
        self.backfill()
        self.backfill()
        assert ReviewAgencyRepair.objects.count() == 1

    def test_backfill_does_not_mint_addresses(self):
        """A new address missing from the table is left blank, not created"""
        agency_task = ReviewAgencyTaskFactory(source="staff")
        self.recorded_task(
            agency_task.agency,
            "a@agency.gov",
            timezone.now().isoformat(),
            new_email="gone@agency.gov",
        )
        self.backfill()
        repair = ReviewAgencyRepair.objects.get()
        assert repair.new_email is None
        assert repair.before["new_email"] == "gone@agency.gov"
        assert not ReviewAgencyTask.objects.filter(email__email="gone@agency.gov")

    def test_backfill_keeps_a_portal_move(self):
        """A portal repair recorded before the history read as no change"""
        agency_task = ReviewAgencyTaskFactory(source="staff")
        self.recorded_task(
            agency_task.agency,
            "seattle@mycusthelp.net",
            timezone.now().isoformat(),
            new_email=None,
            followup_sent=False,
            portal="Seattle GovQA",
        )
        self.backfill()
        repair = ReviewAgencyRepair.objects.get()
        assert repair.new_email is None
        assert repair.portal_display == "Seattle GovQA"


class TestMerges(TestCase):
    """History follows the rows it points at when they are merged"""

    def test_agency_merge_moves_the_repairs(self):
        """A merged agency's history comes with its tasks"""
        good, bad = AgencyFactory(), AgencyFactory()
        repair = ReviewAgencyRepair.objects.create(agency=bad)
        good.merge(bad, UserFactory())
        repair.refresh_from_db()
        assert repair.agency == good

    def test_email_merge_repoints_the_new_address(self):
        """A case variant used as a repair target does not block the merge

        PROTECT would refuse to delete the variant if merge_email_addresses
        did not find this relation to repoint.
        """
        upper, _lower = EmailAddress.objects.bulk_create(
            [EmailAddress(email="New@agency.gov"), EmailAddress(email="new@agency.gov")]
        )
        repair = ReviewAgencyRepair.objects.create(
            agency=AgencyFactory(), new_email=upper
        )
        call_command("merge_email_addresses")
        repair.refresh_from_db()
        assert repair.new_email.email == "new@agency.gov"
        assert EmailAddress.objects.filter(email__iexact="new@agency.gov").count() == 1
