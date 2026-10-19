# -*- coding: utf-8 -*-
"""
Tests for what a staffer is told after acting on a review agency task

A repair that leaves its task open used to vanish: the task dropped to zero
blocked requests, the queue hid it as zero impact, and the only record of the
repair was a raw dict in the generic form data table.  Every action should
say what happened and what is left.
"""

# Django
from django.contrib.messages import get_messages
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

# Standard Library
from unittest import mock

# MuckRock
from muckrock.core.factories import AgencyFactory
from muckrock.core.test_utils import RunCommitHooksMixin
from muckrock.foia.factories import FOIACommunicationFactory
from muckrock.portal.models import Portal
from muckrock.task.forms import ChannelRepairForm
from muckrock.task.tests.test_repair import ChannelRepairMixin
from muckrock.task.tests.test_review_agency import ReviewAgencyQueueMixin

REPAIR = {
    "old_email": "old@agency.gov",
    "new_email": "new@agency.gov",
    "requests_updated": 3,
    "followup_sent": True,
    "agency_info_updated": True,
    "snail_mail": False,
    "by": "staffer",
    "at": "2026-10-06T15:24:15+00:00",
}


class RepairedTaskQueueTests(ReviewAgencyQueueMixin, TestCase):
    """A repaired task stays visible until someone resolves it"""

    def repaired_task(self, **kwargs):
        """An open task whose requests were all moved off by a repair"""
        return self.make_task(blocked=0, form_data={"repair": REPAIR}, **kwargs)

    def test_repaired_open_task_stays_in_the_default_queue(self):
        """Zero blocked because it was repaired, not because it was never live"""
        task = self.repaired_task()
        assert task in self.get_tasks()

    def test_untouched_zero_active_task_is_still_hidden(self):
        quiet = self.make_task(blocked=0)
        assert quiet not in self.get_tasks()

    def test_queue_says_how_many_tasks_are_hidden(self):
        self.make_task(blocked=2)
        self.make_task(blocked=0)
        self.make_task(blocked=0)
        response = self.client.get(self.url)
        assert response.context_data["hidden_count"] == 2
        assert "zero_active=1" in response.context_data["show_hidden_url"]
        self.assertContains(response, "2 tasks with no blocked requests hidden")

    def test_queue_page_and_hidden_notice_share_one_count_of_blocked_requests(self):
        """Each count recomputes every open task's blocked requests"""
        self.make_task(blocked=2)
        self.make_task(blocked=0)
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(self.url)
        # The sidebar counters also count review tasks, but never blocked requests
        task_counts = [
            q["sql"]
            for q in queries.captured_queries
            if q["sql"].startswith("SELECT COUNT")
            and '"task_reviewagencytask"' in q["sql"]
            and '"foia_foiarequest"' in q["sql"]
        ]
        assert len(task_counts) == 1
        assert response.context_data["paginator"].count == 1
        assert response.context_data["hidden_count"] == 1

    def test_hidden_count_respects_the_other_filters(self):
        """Scoped to one agency, another agency's quiet task is not hidden here"""
        active = self.make_task(blocked=2)
        self.make_task(blocked=0)
        response = self.client.get(self.url + "?agency=%d" % active.agency_id)
        assert response.context_data["hidden_count"] == 0
        self.assertNotContains(response, "with no blocked requests hidden")

    def test_show_hidden_link_keeps_the_current_filters(self):
        active = self.make_task(blocked=2)
        self.make_task(blocked=0, agency=active.agency)
        response = self.client.get(self.url + "?agency=%d" % active.agency_id)
        url = response.context_data["show_hidden_url"]
        assert "agency=%d" % active.agency_id in url
        assert "zero_active=1" in url

    def test_nothing_hidden_once_opted_in(self):
        self.make_task(blocked=0)
        response = self.client.get(self.url + "?zero_active=1")
        assert response.context_data["hidden_count"] == 0

    def test_repaired_open_task_is_badged(self):
        self.repaired_task()
        response = self.client.get(self.url)
        self.assertContains(response, "Repaired, not resolved")

    def test_open_task_shows_the_repair_readout_not_the_raw_dict(self):
        task = self.repaired_task()
        response = self.client.get(task.get_absolute_url())
        self.assertContains(response, "Repaired, still open")
        self.assertContains(response, "<code>new@agency.gov</code>", html=True)
        # The generic form data table would print the dict's repr
        self.assertNotContains(response, "&#x27;requests_updated&#x27;")
        # Whether a repair held only means something once it is resolved
        self.assertNotContains(response, "Did it hold?")
        # A multi-line {# #} comment renders as text
        self.assertNotContains(response, "#1869/#1870")

    def test_unrepaired_open_task_has_no_readout(self):
        task = self.make_task(blocked=2)
        response = self.client.get(task.get_absolute_url())
        self.assertNotContains(response, "Repaired, still open")
        self.assertNotContains(response, "What was done")


class RepairFormDefaultsTests(TestCase):
    """Repairing a channel almost always finishes its task"""

    def test_resolve_defaults_on(self):
        assert ChannelRepairForm().fields["resolve"].initial is True


@mock.patch("muckrock.task.tasks.submit_review_update.delay")
class RepairMessageTests(ChannelRepairMixin, RunCommitHooksMixin, TestCase):
    """The message after a repair says what happened and what is left"""

    def message(self, response):
        return " ".join(str(m) for m in get_messages(response.wsgi_request))

    def test_names_the_old_and_new_addresses(self, _mock_delay):
        address, foias, _task = self.make_channel("old@agency.gov", blocked=2)
        response = self.post(
            new_email="new@agency.gov",
            channel_pks=str(address.pk),
            foia_pks=",".join(str(f.pk) for f in foias),
            resolve="on",
        )
        message = self.message(response)
        assert "Rerouted 2 requests on 1 channel (old@agency.gov)" in message
        assert "to new@agency.gov" in message

    def test_reports_followup_and_contact_update(self, _mock_delay):
        address, foias, _task = self.make_channel("old@agency.gov", blocked=2)
        response = self.post(
            new_email="new@agency.gov",
            channel_pks=str(address.pk),
            foia_pks=",".join(str(f.pk) for f in foias),
            update_agency_info="on",
            reply="Please confirm",
            resolve="on",
        )
        message = self.message(response)
        assert "Agency contact updated." in message
        assert "Follow-up queued for 2 requests." in message

    def test_says_when_no_followup_is_sent(self, _mock_delay):
        address, foias, _task = self.make_channel("old@agency.gov")
        response = self.post(
            new_email="new@agency.gov",
            channel_pks=str(address.pk),
            foia_pks=str(foias[0].pk),
            reply="",
            resolve="on",
        )
        assert "No follow-up sent." in self.message(response)

    def test_names_tasks_left_open(self, _mock_delay):
        """The FBI case: every request moved, the task still open"""
        address, foias, task = self.make_channel("old@agency.gov", blocked=2)
        response = self.post(
            new_email="new@agency.gov",
            channel_pks=str(address.pk),
            foia_pks=",".join(str(f.pk) for f in foias),
        )
        message = self.message(response)
        assert "Task #%d (old@agency.gov) is still open." % task.pk in message
        assert "Resolved" not in message

    def test_reports_resolved_tasks(self, _mock_delay):
        address, foias, _task = self.make_channel("old@agency.gov")
        response = self.post(
            new_email="new@agency.gov",
            channel_pks=str(address.pk),
            foia_pks=str(foias[0].pk),
            resolve="on",
        )
        message = self.message(response)
        assert "Resolved 1 task." in message
        assert "still open" not in message

    def test_resolve_only_says_nothing_changed(self, _mock_delay):
        """Resolve on by default makes this easy to do by accident -- say so"""
        address, foias, _task = self.make_channel("old@agency.gov")
        response = self.post(
            channel_pks=str(address.pk),
            foia_pks=str(foias[0].pk),
            reply="Please confirm receipt.",
            resolve="on",
        )
        message = self.message(response)
        assert "No contact change." in message
        assert "Rerouted" not in message
        # the follow up would only bounce off the same broken address
        assert "No follow-up sent." in message


@mock.patch("muckrock.task.tasks.submit_review_update.delay")
class PortalReuseMessageTests(ChannelRepairMixin, RunCommitHooksMixin, TestCase):
    """Matching a known portal URL says whose portal it is

    A shared portal is normal -- city departments often file through one GovQA
    site -- but a mistyped URL can quietly attach another agency's.
    """

    def setUp(self):
        super().setUp()
        self.portal = Portal.objects.create(
            url="https://city.govqa.us", name="City GovQA", type="govqa"
        )
        self.address, foias, _task = self.make_channel("city@mycusthelp.net")
        FOIACommunicationFactory(foia=foias[0], category="n", response=False)
        self.foias = foias

    def repair(self, **data):
        response = self.post(
            repair_via="portal",
            channel_pks=str(self.address.pk),
            foia_pks=str(self.foias[0].pk),
            **data,
        )
        return " ".join(str(m) for m in get_messages(response.wsgi_request))

    def test_names_the_other_agencies_using_a_reused_portal(self, _mock_delay):
        AgencyFactory(portal=self.portal)
        message = self.repair(portal_url="HTTPS://CITY.GOVQA.US")
        assert (
            "Attached the existing portal City GovQA, also used by 1 other agency."
            in message
        )

    def test_says_when_a_reused_portal_has_no_other_agency(self, _mock_delay):
        message = self.repair(portal_url="https://city.govqa.us")
        assert "Attached the existing portal City GovQA." in message

    def test_silent_for_the_agencys_own_portal(self, _mock_delay):
        self.agency.portal = self.portal
        self.agency.save()
        assert "Attached the existing portal" not in self.repair()

    def test_silent_for_a_new_portal(self, _mock_delay):
        message = self.repair(
            portal_url="https://new.govqa.us", portal_name="New", portal_type="govqa"
        )
        assert "Attached the existing portal" not in message


class RepairErrorMessageTests(ChannelRepairMixin, TestCase):
    """Validation errors say which field they are about"""

    def test_field_errors_name_the_field(self):
        self.make_channel("old@agency.gov")
        response = self.post()
        messages = [str(m) for m in get_messages(response.wsgi_request)]
        assert any(m.startswith("Replacement email address: ") for m in messages)
        # Not Django's bulleted error list
        assert not any(m.startswith("*") for m in messages)
