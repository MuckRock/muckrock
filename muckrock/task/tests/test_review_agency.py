# -*- coding: utf-8 -*-
"""
Tests for the review agency task queue and the agency detail view

These cover the two user visible surfaces of the channel work: the impact
ordered queue, and the per agency detail view that replaces the inline AJAX
panel.
"""

# Django
from django.conf import settings
from django.db import connection, reset_queries
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

# Standard Library
import json
import re
from datetime import timedelta

# MuckRock
from muckrock.communication.factories import (
    EmailAddressFactory,
    EmailCommunicationFactory,
    PhoneNumberFactory,
)
from muckrock.communication.models import EmailError
from muckrock.core.factories import (
    AgencyEmailFactory,
    AgencyFactory,
    AgencyPhoneFactory,
    UserFactory,
)
from muckrock.foia.factories import FOIARequestFactory
from muckrock.task.constants import REVIEW_AGENCY_FOLLOWUP
from muckrock.task.factories import ReviewAgencyTaskFactory
from muckrock.task.models import ReviewAgencyTask


class ReviewAgencyQueueMixin:
    """Shared setup for the queue tests"""

    # pylint: disable=invalid-name
    def setUp(self):
        password = "abc"
        self.user = UserFactory(is_staff=True, password=password)
        self.url = reverse("review-agency-task-list")
        self.client.login(username=self.user.username, password=password)

    def make_task(self, blocked=0, source="email", agency=None, **kwargs):
        """A task on one channel, blocking some number of open requests"""
        agency = agency or AgencyFactory(email=None, fax=None)
        address = EmailAddressFactory(status="error")
        AgencyEmailFactory(agency=agency, email=address)
        if blocked:
            FOIARequestFactory.create_batch(
                blocked, agency=agency, email=address, status="ack"
            )
        return ReviewAgencyTaskFactory(
            agency=agency, source=source, email=address, resolved=False, **kwargs
        )

    def get_tasks(self, query=""):
        """The task list the view renders, in order"""
        response = self.client.get(self.url + query)
        assert response.status_code == 200
        return list(response.context_data["object_list"])


class ReviewAgencyTaskImpactOrderingTests(ReviewAgencyQueueMixin, TestCase):
    """The queue orders and reads by blocked request impact

    Today every task looks equivalent: one blocking 1,075 FBI requests reads
    the same as one blocking a single request at a local library.  Blocked
    count is the ordering key, always -- never channel count, never age.
    """

    def test_default_ordering_is_impact(self):
        """A task blocking 100 precedes one blocking 1"""
        small = self.make_task(blocked=1)
        big = self.make_task(blocked=7)
        medium = self.make_task(blocked=3)
        assert self.get_tasks() == [big, medium, small]

    def test_impact_beats_creation_date(self):
        """Age does not reorder the queue"""
        old_small = self.make_task(blocked=1)
        new_big = self.make_task(blocked=5)
        ReviewAgencyTask.objects.filter(pk=old_small.pk).update(
            date_created=timezone.now() - timedelta(days=900)
        )
        assert self.get_tasks()[0] == new_big

    def test_sort_by_date_created_still_works(self):
        """Impact is the default order, not the only one"""
        first = self.make_task(blocked=1)
        second = self.make_task(blocked=9)
        ReviewAgencyTask.objects.filter(pk=first.pk).update(
            date_created=timezone.now() - timedelta(days=10)
        )
        tasks = self.get_tasks("?sort=date_created&order=asc")
        assert tasks == [first, second]

    def test_blocked_count_annotated_on_each_task(self):
        """The count is legible without expanding anything"""
        self.make_task(blocked=4)
        assert self.get_tasks()[0].blocked_count == 4

    def test_null_channel_task_counts_all_agency_open_requests(self):
        """A staff or stale task is about the agency, so it counts the agency"""
        agency = AgencyFactory(email=None, fax=None)
        address = EmailAddressFactory(status="error")
        FOIARequestFactory.create_batch(3, agency=agency, email=address, status="ack")
        task = ReviewAgencyTaskFactory(
            agency=agency, source="staff", email=None, resolved=False
        )
        tasks = self.get_tasks()
        assert next(t for t in tasks if t.pk == task.pk).blocked_count == 3

    def count_queries(self):
        """Queries for one rendering of the list"""
        try:
            settings.DEBUG = True
            reset_queries()
            assert self.client.get(self.url).status_code == 200
            return len(connection.queries)
        finally:
            settings.DEBUG = False
            reset_queries()

    def test_query_count_does_not_grow_with_the_queue(self):
        """Annotating impact must not cost a query per task

        Measured after a warm up request: the first render of any task list
        also populates the content type and config caches, which is why the
        shared n_plus_one_query helper reads high on a cold client.
        """
        self.make_task(blocked=2)
        self.count_queries()
        one_task = self.count_queries()

        for _ in range(4):
            self.make_task(blocked=3)
        many_tasks = self.count_queries()

        assert one_task == many_tasks

    def test_channel_summary_costs_no_extra_queries(self):
        """The summary is annotated, not fetched per row"""
        self.make_task(blocked=2)
        self.count_queries()
        before = self.count_queries()
        for _ in range(4):
            self.make_task(blocked=2)
        assert self.count_queries() == before


class ReviewAgencyTaskQueueFilterTests(ReviewAgencyQueueMixin, TestCase):
    """The filters staff need to work the queue"""

    def test_min_blocked_filter(self):
        """Isolate the head of the queue"""
        self.make_task(blocked=3)
        big = self.make_task(blocked=12)
        assert self.get_tasks("?min_blocked=10") == [big]

    def test_max_blocked_filter(self):
        """Isolate the tail of the queue"""
        small = self.make_task(blocked=2)
        self.make_task(blocked=12)
        assert self.get_tasks("?max_blocked=5&zero_active=1") == [small]

    def test_unlabeled_source_filter(self):
        """Unlabeled tasks are filterable, which they are not today

        The filter only offered the four labelled sources, so the tasks that
        predate source labelling -- overwhelmingly email problems -- could not
        be reached at all.
        """
        unlabeled = self.make_task(blocked=2, source=None)
        self.make_task(blocked=3, source="email")
        assert self.get_tasks("?source=unlabeled") == [unlabeled]

    def test_email_source_filter_excludes_unlabeled(self):
        """Asking for email does not sweep in the unlabeled tasks"""
        self.make_task(blocked=2, source=None)
        email_task = self.make_task(blocked=3, source="email")
        assert self.get_tasks("?source=email") == [email_task]

    def test_zero_active_excluded_by_default(self):
        """Zero active is a triage hint, not a resolve trigger

        639 agencies have an open task and no active requests.  They are not
        auto-resolve candidates -- the address is still broken and the next
        request in hits the same wall -- so they are defaulted out of the
        impact ordered view rather than closed.
        """
        active = self.make_task(blocked=2)
        quiet = self.make_task(blocked=0)
        tasks = self.get_tasks()
        assert active in tasks
        assert quiet not in tasks

    def test_zero_active_opt_in(self):
        """Staff can opt into the quiet tasks for preventative repair"""
        quiet = self.make_task(blocked=0)
        assert quiet in self.get_tasks("?zero_active=1")

    def test_agency_grouping_key_in_context(self):
        """Twelve State Department rows must not read as twelve unrelated items"""
        agency = AgencyFactory(email=None, fax=None)
        self.make_task(blocked=5, agency=agency)
        self.make_task(blocked=3, agency=agency)
        self.make_task(blocked=4)
        groups = self.client.get(self.url).context_data["agency_groups"]
        assert groups[agency.pk] == 2

    def test_an_agencys_channels_stay_together(self):
        """Agencies are ordered by total impact, channels within them by theirs

        Ordering on channel impact alone would interleave a heavy agency's
        smaller channels with other agencies' rows, which is the reading the
        design is trying to prevent.  The agency's total is what competes for
        position in the queue; its channels sort inside that.
        """
        heavy = AgencyFactory(email=None, fax=None)
        heavy_big = self.make_task(blocked=5, agency=heavy)
        heavy_small = self.make_task(blocked=3, agency=heavy)
        middle = self.make_task(blocked=4)
        assert self.get_tasks() == [heavy_big, heavy_small, middle]

    def test_agency_total_blocked_annotated(self):
        """The agency level total is legible on the row"""
        agency = AgencyFactory(email=None, fax=None)
        self.make_task(blocked=5, agency=agency)
        self.make_task(blocked=3, agency=agency)
        assert self.get_tasks()[0].agency_blocked_count == 8

    def test_row_carries_the_channel_summary(self):
        """The row is legible without expanding anything

        Which channel is broken, how it is broken, and how recently -- so a
        staffer can triage from the queue rather than opening every task.
        """
        task_ = self.make_task(blocked=2)
        EmailError.objects.create(
            email=EmailCommunicationFactory(),
            datetime=timezone.now() - timedelta(days=4),
            recipient=task_.email,
            code="550",
            error="no such mailbox",
            event="failed",
            reason="bounce",
        )
        row = self.get_tasks()[0]
        assert row.channel.address == task_.email
        assert row.channel.blocked_count == 2
        assert row.channel.last_error_code == "550"
        assert row.channel.last_error_age == 4
        assert row.channel.classification == "dead"

    def test_row_marks_a_portal_channel(self):
        """A portal address must be visually distinct, not invite an email swap"""
        agency = AgencyFactory(email=None, fax=None)
        address = EmailAddressFactory(email="seattle@mycusthelp.net", status="error")
        AgencyEmailFactory(agency=agency, email=address)
        FOIARequestFactory.create_batch(3, agency=agency, email=address, status="ack")
        ReviewAgencyTaskFactory(
            agency=agency, source="email", email=address, resolved=False
        )
        row = self.get_tasks()[0]
        assert row.channel.is_portal
        assert row.channel.classification == "portal"

    def test_row_channel_is_none_for_an_agency_level_task(self):
        """A staff or stale task has no channel, and says so rather than lying"""
        agency = AgencyFactory(email=None, fax=None)
        address = EmailAddressFactory(status="error")
        FOIARequestFactory(agency=agency, email=address, status="ack")
        ReviewAgencyTaskFactory(
            agency=agency, source="staff", email=None, resolved=False
        )
        assert self.get_tasks()[0].channel is None

    def test_row_reports_primary_status(self):
        """Whether the broken channel is the agency's primary contact"""
        task_ = self.make_task(blocked=2)
        task_.agency.agencyemail_set.update(request_type="primary", email_type="to")
        assert self.get_tasks()[0].channel.is_primary

    def test_channel_summary_costs_no_extra_queries(self):
        """The summary is annotated, not fetched per row"""
        self.make_task(blocked=2)
        self.count_queries()
        before = self.count_queries()
        for _ in range(4):
            self.make_task(blocked=2)
        assert self.count_queries() == before

    def count_queries(self):
        """Queries for one rendering of the list"""
        try:
            settings.DEBUG = True
            reset_queries()
            assert self.client.get(self.url).status_code == 200
            return len(connection.queries)
        finally:
            settings.DEBUG = False
            reset_queries()

    def test_query_count_does_not_grow_with_the_queue(self):
        """Annotating impact must not cost a query per task

        Measured after a warm up request: the first render of any task list
        also populates the content type and config caches, which is why the
        shared n_plus_one_query helper reads high on a cold client.
        """
        self.make_task(blocked=2)
        self.count_queries()
        one_task = self.count_queries()

        for _ in range(4):
            self.make_task(blocked=3)
        many_tasks = self.count_queries()

        assert one_task == many_tasks


class ReviewAgencyDetailViewTests(TestCase):
    """The agency detail view -- one URL for one agency's whole channel roster

    Whether an agency's load is concentrated on one mailbox or spread across
    22, the work is the roster, and a roster deserves a real URL: shareable in
    Slack and tickets, with a working back button, and heavy work that does not
    push the queue off screen.
    """

    def setUp(self):
        password = "abc"
        self.user = UserFactory(is_staff=True, password=password)
        self.agency = AgencyFactory(email=None, fax=None)
        self.url = reverse("review-agency-detail", kwargs={"pk": self.agency.pk})
        self.client.login(username=self.user.username, password=password)

    def make_channel(self, email, blocked=0, status="error"):
        """Attach an address to the agency with some blocked traffic"""
        address = EmailAddressFactory(email=email, status=status)
        AgencyEmailFactory(agency=self.agency, email=address)
        if blocked:
            FOIARequestFactory.create_batch(
                blocked, agency=self.agency, email=address, status="ack"
            )
        return address

    def context(self):
        """The rendered context"""
        response = self.client.get(self.url)
        assert response.status_code == 200
        return response.context

    def test_staff_can_view(self):
        """Staff get the page"""
        assert self.client.get(self.url).status_code == 200

    def test_non_staff_is_turned_away(self):
        """A non staff user cannot reach it"""
        self.client.logout()
        password = "abc"
        user = UserFactory(is_staff=False, password=password)
        self.client.login(username=user.username, password=password)
        assert self.client.get(self.url).status_code in (302, 403)

    def test_anonymous_is_turned_away(self):
        """Anonymous users cannot reach it"""
        self.client.logout()
        assert self.client.get(self.url).status_code in (302, 403)

    def test_unknown_agency_is_404(self):
        """A bad pk is a 404, not a crash"""
        self.client.logout()
        password = "abc"
        user = UserFactory(is_staff=True, password=password)
        self.client.login(username=user.username, password=password)
        assert (
            self.client.get(
                reverse("review-agency-detail", kwargs={"pk": 99999999})
            ).status_code
            == 404
        )

    def test_agency_identity_and_rollup(self):
        """Identity plus the scorecard that says how much work is left"""
        self.make_channel("big@fbi.gov", blocked=6)
        self.make_channel("small@fbi.gov", blocked=1)
        self.make_channel("healthy@fbi.gov", blocked=0, status="good")
        context = self.context()
        assert context["agency"] == self.agency
        assert context["total_blocked"] == 7
        assert context["channels_known"] == 3
        assert context["channels_broken"] == 2
        assert context["channels_active"] == 2
        assert "last_success" in context

    def test_primary_email_in_contact_info(self):
        """The primary to address is shown even when it is broken

        A broken primary is the usual reason the agency is in review, so the
        good-only Agency.email would hide exactly the address that matters.
        """
        self.make_channel("broken@fbi.gov", status="error")
        AgencyEmailFactory(
            agency=self.agency,
            email=EmailAddressFactory(email="cc@fbi.gov"),
            email_type="cc",
        )
        AgencyEmailFactory(
            agency=self.agency,
            email=EmailAddressFactory(email="appeal@fbi.gov"),
            request_type="appeal",
        )
        context = self.context()
        assert [e.email.email for e in context["primary_emails"]] == ["broken@fbi.gov"]

    def test_channels_present_and_impact_ordered(self):
        """The roster, most blocked first"""
        self.make_channel("small@fbi.gov", blocked=1)
        self.make_channel("big@fbi.gov", blocked=8)
        channels = self.context()["channels"]
        assert [c.address.email for c in channels] == [
            "big@fbi.gov",
            "small@fbi.gov",
        ]

    def test_a_merged_mailbox_appears_once(self):
        """Post merge the roster shows mailboxes, not rows

        A regression check on the whole point of the address merge: listed as
        three channels, a staffer fixes one while the other two keep failing.
        """
        self.make_channel("foipaquestions@fbi.gov", blocked=9)
        channels = self.context()["channels"]
        matching = [c for c in channels if c.address.email == "foipaquestions@fbi.gov"]
        assert len(matching) == 1
        assert matching[0].blocked_count == 9

    def test_healthy_channels_are_present_and_marked(self):
        """Staff choosing a replacement need to see a working alternate

        Hiding them pushes that lookup to the admin page and breaks flow.
        """
        self.make_channel("broken@fbi.gov", blocked=2, status="error")
        self.make_channel("working@fbi.gov", blocked=0, status="good")
        channels = {c.address.email: c for c in self.context()["channels"]}
        assert "working@fbi.gov" in channels
        assert not channels["working@fbi.gov"].has_error
        assert channels["broken@fbi.gov"].has_error

    def test_portal_channel_flags_email_repair_as_wrong(self):
        """Seattle PD's largest channel is a GovQA address

        No replacement email repairs it -- picking one would be actively
        wrong -- so the view has to say so rather than invite the swap.
        """
        self.make_channel("seattle@mycusthelp.net", blocked=159)
        context = self.context()
        channel = context["channels"][0]
        assert channel.is_portal
        assert context["has_portal_channel"]

    def test_contact_info_at_hand(self):
        """Website and phone are one click away for finding new contact info"""
        self.agency.website = "https://www.fbi.gov"
        self.agency.save()
        AgencyPhoneFactory(
            agency=self.agency, phone=PhoneNumberFactory(number="617-555-0100")
        )
        AgencyPhoneFactory(
            agency=self.agency,
            phone=PhoneNumberFactory(number="617-555-0199", type="fax"),
            request_type="primary",
        )
        response = self.client.get(self.url)
        content = response.content.decode()
        # Collapsed so the checks do not depend on the template's indentation
        start = content.index('class="review-agency-contact"')
        end = content.index("</dl>", start)
        contact = re.sub(r"\s+", " ", content[start:end])
        assert '<a href="https://www.fbi.gov"' in contact
        assert 'href="tel:+16175550100"' in contact
        # The number's own type is not repeated under its label
        assert "(617) 555-0199 (primary)" in contact
        assert "(phone)" not in contact
        # Email, addresses and the FOIA web page are empty, and say so
        assert contact.count("None on record") == 3

    def test_json_payload_round_trips(self):
        """The Svelte handoff: props in, no fetches"""
        self.make_channel("foia@fbi.gov", blocked=3)
        response = self.client.get(self.url)
        payload = json.loads(
            re.search(
                rb'<script id="review-agency-data" '
                rb'type="application/json">(.*?)</script>',
                response.content,
                re.DOTALL,
            )
            .group(1)
            .decode()
        )
        assert payload["agency"]["id"] == self.agency.pk
        assert payload["total_blocked"] == 3
        channel = payload["channels"][0]
        assert channel["email"] == "foia@fbi.gov"
        assert channel["blocked_count"] == 3
        assert channel["classification"] == "dead"
        assert len(channel["foias"]) == 3

    def test_follow_up_defaults_to_legacy_text(self):
        """The follow-up starts from the same text the legacy task offers"""
        response = self.client.get(self.url)
        payload = json.loads(
            re.search(
                rb'<script id="review-agency-data" '
                rb'type="application/json">(.*?)</script>',
                response.content,
                re.DOTALL,
            )
            .group(1)
            .decode()
        )
        assert payload["default_reply"] == REVIEW_AGENCY_FOLLOWUP
        # The no-JS fallback form starts from it too
        assert response.context["repair_form"]["reply"].value() == (
            REVIEW_AGENCY_FOLLOWUP
        )

    def test_query_count_is_constant(self):
        """A 20 channel agency must not cost 20 times a 1 channel agency"""

        def count():
            try:
                settings.DEBUG = True
                reset_queries()
                assert self.client.get(self.url).status_code == 200
                return len(connection.queries)
            finally:
                settings.DEBUG = False
                reset_queries()

        self.make_channel("one@fbi.gov", blocked=1)
        count()
        one_channel = count()
        for index in range(20):
            self.make_channel("many%d@fbi.gov" % index, blocked=1)
        assert count() == one_channel
