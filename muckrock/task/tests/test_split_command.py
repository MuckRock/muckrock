# -*- coding: utf-8 -*-
"""
Tests for the retroactive per-channel task split

Existing tasks are keyed on (agency, source) and do not record which channel
triggered them.  This splits them into one task per channel carrying blocked
active traffic -- strategy 3 -- which shrinks the queue rather than exploding
it, and makes every task say what is actually broken.
"""

# Django
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

# Standard Library
from io import StringIO

# Third Party
import pytest

# MuckRock
from muckrock.communication.factories import EmailAddressFactory
from muckrock.communication.models import EmailAddress
from muckrock.core.factories import AgencyEmailFactory, AgencyFactory
from muckrock.foia.factories import FOIARequestFactory
from muckrock.task.factories import ReviewAgencyTaskFactory
from muckrock.task.models import ReviewAgencyTask


class TestSplitReviewAgencyTasks(TestCase):
    """Test the split_review_agency_tasks command"""

    def setUp(self):
        self.agency = AgencyFactory(email=None, fax=None)

    def call(self, *args):
        """Run the command, returning its stdout"""
        out = StringIO()
        call_command("split_review_agency_tasks", *args, stdout=out)
        return out.getvalue()

    def channel(self, email, blocked=1, status="error"):
        """An address on the agency, optionally carrying blocked traffic"""
        address = EmailAddressFactory(email=email, status=status)
        AgencyEmailFactory(agency=self.agency, email=address)
        if blocked:
            FOIARequestFactory.create_batch(
                blocked, agency=self.agency, email=address, status="ack"
            )
        return address

    def legacy_task(self, source="email"):
        """A task in the old shape: no channel"""
        return ReviewAgencyTaskFactory(
            agency=self.agency, source=source, email=None, resolved=False
        )

    def test_single_channel_agency_gets_exactly_one_task(self):
        """The 81.7% majority case"""
        address = self.channel("foia@agency.gov", blocked=3)
        original = self.legacy_task()
        self.call()
        new_tasks = ReviewAgencyTask.objects.filter(agency=self.agency, resolved=False)
        assert new_tasks.count() == 1
        assert new_tasks.get().email == address
        original.refresh_from_db()
        assert original.resolved

    def test_multi_channel_agency_gets_one_task_per_channel(self):
        """The FBI shape, at a scale we can assert exactly"""
        first = self.channel("foipaquestions@fbi.gov", blocked=9)
        second = self.channel("foia@fbi.gov", blocked=2)
        third = self.channel("records@fbi.gov", blocked=1)
        self.legacy_task()
        self.call()
        new_tasks = ReviewAgencyTask.objects.filter(agency=self.agency, resolved=False)
        assert new_tasks.count() == 3
        assert {t.email for t in new_tasks} == {first, second, third}

    def test_a_merged_mailbox_is_one_task_not_three(self):
        """The point of merging first

        Split before the merge, one mailbox becomes three tasks and a staffer
        fixes one while the other two keep failing.
        """
        address = self.channel("foipaquestions@fbi.gov", blocked=9)
        self.legacy_task()
        self.call()
        tasks = ReviewAgencyTask.objects.filter(
            agency=self.agency, email=address, resolved=False
        )
        assert tasks.count() == 1

    def test_channels_with_no_blocked_traffic_get_no_task(self):
        """Strategy 3: a channel earns a task by carrying live traffic

        Counting every error flagged link instead yields 4,562 channels --
        inflated by stale flags, half of which carry nothing.
        """
        self.channel("carrying@agency.gov", blocked=2)
        self.channel("quiet@agency.gov", blocked=0)
        self.legacy_task()
        self.call()
        emails = {
            t.email.email
            for t in ReviewAgencyTask.objects.filter(agency=self.agency, resolved=False)
        }
        assert emails == {"carrying@agency.gov"}

    def test_zero_active_agency_gets_no_task(self):
        """Nothing to route, so nothing to split"""
        self.channel("quiet@agency.gov", blocked=0)
        original = self.legacy_task()
        self.call()
        assert not ReviewAgencyTask.objects.filter(
            agency=self.agency, resolved=False
        ).exists()
        original.refresh_from_db()
        assert original.resolved

    def test_metadata_is_preserved(self):
        """date_created and source carry over"""
        self.channel("foia@agency.gov", blocked=1)
        original = self.legacy_task(source="email")
        self.call()
        new_task = ReviewAgencyTask.objects.get(agency=self.agency, resolved=False)
        assert new_task.source == "email"
        assert new_task.date_created == original.date_created

    def test_null_source_stays_null(self):
        """Unlabeled tasks stay unlabeled rather than being guessed at"""
        self.channel("foia@agency.gov", blocked=1)
        self.legacy_task(source=None)
        self.call()
        assert (
            ReviewAgencyTask.objects.get(agency=self.agency, resolved=False).source
            is None
        )

    def test_original_is_resolved_never_deleted(self):
        """Never delete -- the audit trail is the point"""
        self.channel("foia@agency.gov", blocked=1)
        original = self.legacy_task()
        self.call()
        original.refresh_from_db()
        assert original.resolved
        assert original.pk

    def test_original_note_points_at_its_successors(self):
        """A staffer looking at the old task can find where the work went"""
        address = self.channel("foia@agency.gov", blocked=1)
        original = self.legacy_task()
        self.call()
        original.refresh_from_db()
        assert address.email in original.note

    def test_already_split_tasks_are_left_alone(self):
        """A task that already has a channel needs no splitting"""
        address = self.channel("foia@agency.gov", blocked=1)
        existing = ReviewAgencyTaskFactory(
            agency=self.agency, source="email", email=address, resolved=False
        )
        self.call()
        existing.refresh_from_db()
        assert not existing.resolved
        assert (
            ReviewAgencyTask.objects.filter(agency=self.agency, resolved=False).count()
            == 1
        )

    def test_rerun_is_a_noop(self):
        """Running again changes nothing"""
        self.channel("foia@agency.gov", blocked=1)
        self.legacy_task()
        self.call()
        before = set(ReviewAgencyTask.objects.values_list("pk", "email", "resolved"))
        self.call()
        after = set(ReviewAgencyTask.objects.values_list("pk", "email", "resolved"))
        assert before == after

    def test_dry_run_writes_nothing(self):
        """--dry-run reports the plan and changes no rows"""
        self.channel("foia@agency.gov", blocked=1)
        self.legacy_task()
        before = set(ReviewAgencyTask.objects.values_list("pk", "email", "resolved"))
        output = self.call("--dry-run")
        after = set(ReviewAgencyTask.objects.values_list("pk", "email", "resolved"))
        assert before == after
        assert "foia@agency.gov" in output

    def test_refuses_to_run_on_unmerged_addresses(self):
        """The merge has to have happened first

        With a case variant still in the table, one mailbox would become two
        tasks -- which is precisely the split the merge exists to prevent.
        """
        EmailAddress.objects.bulk_create(
            [EmailAddress(email="Mixed@agency.gov", status="error")]
        )
        self.channel("foia@agency.gov", blocked=1)
        self.legacy_task()
        with pytest.raises(CommandError) as excinfo:
            self.call()
        assert (
            "lowercase" in str(excinfo.value).lower()
            or "merge" in str(excinfo.value).lower()
        )

    def test_resolved_tasks_are_not_split(self):
        """Only the open queue is migrated"""
        self.channel("foia@agency.gov", blocked=1)
        resolved = ReviewAgencyTaskFactory(
            agency=self.agency, source="email", email=None, resolved=True
        )
        self.call()
        resolved.refresh_from_db()
        assert resolved.email is None
        assert resolved.note == ""
        # nothing new was emitted for an already resolved task
        assert ReviewAgencyTask.objects.filter(agency=self.agency).count() == 1
