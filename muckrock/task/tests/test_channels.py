# -*- coding: utf-8 -*-
"""
Tests for the channel layer

A channel is one of an agency's communication mailboxes.  This layer answers,
for one agency: what are its real mailboxes, which are broken, how are they
broken, and how much live traffic each one is blocking.  The queue, the detail
view and the repair form all read the same answer from here.
"""

# Django
from django.test import TestCase
from django.utils import timezone

# Standard Library
from datetime import timedelta

# MuckRock
from muckrock.communication.factories import (
    EmailAddressFactory,
    EmailCommunicationFactory,
)
from muckrock.communication.models import EmailAddress, EmailError
from muckrock.core.factories import AgencyEmailFactory, AgencyFactory
from muckrock.foia.factories import FOIARequestFactory
from muckrock.task.channels import (
    STALE_ERROR_DAYS,
    Channel,
    agency_channels,
    agency_rollup,
    classify_channel,
)


def add_error(address, code="550", reason="", days_ago=1, error="no such mailbox"):
    """Attach an error event to an address"""
    return EmailError.objects.create(
        email=EmailCommunicationFactory(),
        datetime=timezone.now() - timedelta(days=days_ago),
        recipient=address,
        code=code,
        error=error,
        event="failed",
        reason=reason,
    )


class TestClassifyChannel(TestCase):
    """Channels fail in distinct ways and each needs a different repair"""

    def classify(self, email, errors=()):
        """Classify an address by its string"""
        return classify_channel(EmailAddress.objects.fetch(email), errors)

    def test_govqa_portal_address(self):
        """A GovQA notification sender is a portal, not a dead mailbox"""
        assert self.classify("seattle@mycusthelp.net") == "portal"

    def test_secure_release_portal_address(self):
        """SecureRelease notification sender"""
        assert self.classify("noreply@securerelease.us") == "portal"

    def test_foiaonline_portal_address(self):
        """FOIAonline notification sender"""
        assert self.classify("no-reply@foiaonline.gov") == "portal"

    def test_state_portal_address(self):
        """State's portal notification sender"""
        assert self.classify("noreply@mail.foia.state.gov") == "portal"

    def test_portal_beats_noreply(self):
        """A portal address whose local part is no-reply is still a portal

        This matters: told it is a no-reply, staff would look for the agency's
        real mailbox; told it is a portal, they know email is the wrong tool.
        """
        assert self.classify("no-reply@foiaonline.gov") == "portal"

    def test_donotreply_address(self):
        """A do-not-reply address we harvested and then mailed"""
        assert self.classify("donotreply@hq.dhs.gov") == "noreply"

    def test_no_reply_address(self):
        """Hyphenated no-reply"""
        assert self.classify("no-reply@example.gov") == "noreply"

    def test_postmaster_address(self):
        """postmaster is never a FOIA contact"""
        assert self.classify("postmaster@usdoj.gov") == "noreply"

    def test_notification_address(self):
        """notification@ senders"""
        assert self.classify("notification@pay.gov") == "noreply"

    def test_dead_mailbox_is_the_default(self):
        """An ordinary address with a 550 is a dead mailbox"""
        address = EmailAddress.objects.fetch("foia@example.gov")
        error = add_error(address, code="550")
        assert classify_channel(address, [error]) == "dead"

    def test_blacklisted_is_a_reputation_problem(self):
        """A sender side reputation failure, which no address swap fixes"""
        address = EmailAddress.objects.fetch("foia@example.gov")
        error = add_error(address, code="550", reason="blacklisted")
        assert classify_channel(address, [error]) == "reputation"

    def test_espblock_is_a_reputation_problem(self):
        """espblock is the other reputation reason"""
        address = EmailAddress.objects.fetch("foia@example.gov")
        error = add_error(address, code="554", reason="espblock")
        assert classify_channel(address, [error]) == "reputation"

    def test_reputation_only_from_the_newest_error(self):
        """An old reputation block does not mask a current dead mailbox"""
        address = EmailAddress.objects.fetch("foia@example.gov")
        old = add_error(address, reason="blacklisted", days_ago=400)
        new = add_error(address, code="550", reason="", days_ago=1)
        assert classify_channel(address, [new, old]) == "dead"


class TestErrorTranslation(TestCase):
    """SMTP codes read as plain language, not as numbers"""

    def channel(self, code, reason=""):
        """A channel carrying one error"""
        address = EmailAddress.objects.fetch("foia@example.gov")
        return Channel(address=address, last_error_code=code, last_error_reason=reason)

    def test_550_is_the_common_case(self):
        """71% of these errors are a 550"""
        assert "does not exist" in self.channel("550").last_error_message.lower()

    def test_reputation_reason_beats_the_code(self):
        """A reputation block needs a different job, so it says so

        No address swap fixes this.  Reading it as a dead mailbox would send a
        staffer looking for a replacement address that cannot help.
        """
        message = self.channel("550", reason="blacklisted").last_error_message
        assert "blocked" in message.lower() or "reputation" in message.lower()

    def test_unknown_code_falls_back_to_the_code(self):
        """An unmapped code still tells you something"""
        assert "521" in self.channel("521").last_error_message

    def test_no_error_has_no_message(self):
        """Nothing to translate"""
        assert self.channel("").last_error_message == ""


class TestAgencyChannels(TestCase):
    """The roster for one agency"""

    def setUp(self):
        self.agency = AgencyFactory(email=None, fax=None)

    def make_channel(self, email, blocked=0, status="error", request_type="primary"):
        """Attach an address to the agency with some blocked traffic"""
        address = EmailAddressFactory(email=email, status=status)
        AgencyEmailFactory(
            agency=self.agency,
            email=address,
            request_type=request_type,
            email_type="to",
        )
        if blocked:
            FOIARequestFactory.create_batch(
                blocked, agency=self.agency, email=address, status="ack"
            )
        return address

    def test_one_row_per_mailbox(self):
        """Post merge there is one row per mailbox, so one channel per row"""
        self.make_channel("foipaquestions@fbi.gov", blocked=6)
        self.make_channel("foia@fbi.gov", blocked=2)
        channels = agency_channels(self.agency)
        assert len(channels) == 2
        assert [c.address.email for c in channels] == [
            "foipaquestions@fbi.gov",
            "foia@fbi.gov",
        ]

    def test_sorted_by_blocked_count_descending(self):
        """Impact orders the roster"""
        self.make_channel("small@fbi.gov", blocked=1)
        self.make_channel("big@fbi.gov", blocked=9)
        self.make_channel("medium@fbi.gov", blocked=4)
        channels = agency_channels(self.agency)
        assert [c.blocked_count for c in channels] == [9, 4, 1]

    def test_no_case_collapse_in_this_layer(self):
        """A surviving variant is a data bug, not something this layer hides

        The channel layer keys on the address row.  If two rows for one mailbox
        reach it, it reports two channels -- which is how the merge command's
        job stays visible instead of being silently papered over.
        """
        EmailAddress.objects.bulk_create(
            [
                EmailAddress(email="Split@fbi.gov", status="error"),
                EmailAddress(email="split@fbi.gov", status="error"),
            ]
        )
        for address in EmailAddress.objects.filter(email__iexact="split@fbi.gov"):
            AgencyEmailFactory(agency=self.agency, email=address)
        assert len(agency_channels(self.agency)) == 2

    def test_stale_error_flag_with_no_traffic_is_not_active(self):
        """An error flag on an address carrying nothing is not an active channel"""
        self.make_channel("stale@fbi.gov", blocked=0)
        channel = agency_channels(self.agency)[0]
        assert channel.blocked_count == 0
        assert not channel.is_active

    def test_traffic_makes_a_channel_active_even_when_the_link_is_clean(self):
        """An address with open requests is active regardless of its flag"""
        address = self.make_channel("clean@fbi.gov", blocked=3, status="good")
        channels = agency_channels(self.agency)
        channel = next(c for c in channels if c.address == address)
        assert channel.is_active
        assert not channel.has_error

    def test_includes_an_address_with_traffic_but_no_agency_link(self):
        """A request can be routed at an address the roster never listed"""
        orphan = EmailAddressFactory(email="orphan@fbi.gov", status="error")
        FOIARequestFactory(agency=self.agency, email=orphan, status="ack")
        addresses = [c.address for c in agency_channels(self.agency)]
        assert orphan in addresses

    def test_healthy_channels_are_included_and_marked(self):
        """Staff choosing a replacement need to see a working alternate"""
        self.make_channel("broken@fbi.gov", blocked=2, status="error")
        self.make_channel("working@fbi.gov", blocked=0, status="good")
        channels = {c.address.email: c for c in agency_channels(self.agency)}
        assert channels["broken@fbi.gov"].has_error
        assert not channels["working@fbi.gov"].has_error

    def test_primary_flag(self):
        """Whether this is the agency's primary contact"""
        self.make_channel("primary@fbi.gov", request_type="primary")
        self.make_channel("other@fbi.gov", request_type="none")
        channels = {c.address.email: c for c in agency_channels(self.agency)}
        assert channels["primary@fbi.gov"].is_primary
        assert not channels["other@fbi.gov"].is_primary

    def test_error_recency_exposed(self):
        """Last error, its code and reason, and its age"""
        address = self.make_channel("foia@fbi.gov", blocked=1)
        add_error(address, code="550", reason="bounce", days_ago=3)
        channel = agency_channels(self.agency)[0]
        assert channel.last_error is not None
        assert channel.last_error_code == "550"
        assert channel.last_error_reason == "bounce"
        assert channel.last_error_age == 3
        assert channel.error_count == 1

    def test_old_error_is_flagged_stale(self):
        """An error flag with no bounce in two years is itself a signal"""
        address = self.make_channel("old@fbi.gov", blocked=1)
        add_error(address, days_ago=STALE_ERROR_DAYS + 10)
        channel = agency_channels(self.agency)[0]
        assert channel.is_stale_error

    def test_recent_error_is_not_stale(self):
        """A live breakage is not stale"""
        address = self.make_channel("new@fbi.gov", blocked=1)
        add_error(address, days_ago=5)
        channel = agency_channels(self.agency)[0]
        assert not channel.is_stale_error

    def test_error_flag_with_no_events_is_not_stale(self):
        """No error events at all is unknown, not stale"""
        self.make_channel("flagged@fbi.gov", blocked=1)
        channel = agency_channels(self.agency)[0]
        assert channel.last_error is None
        assert not channel.is_stale_error

    def test_foias_attached_per_channel(self):
        """The requests currently routed to a channel"""
        self.make_channel("foia@fbi.gov", blocked=3)
        channel = agency_channels(self.agency)[0]
        assert len(channel.foias) == 3

    def test_classification_present_on_each_channel(self):
        """Each channel carries its failure class"""
        self.make_channel("seattle@mycusthelp.net", blocked=5)
        channel = agency_channels(self.agency)[0]
        assert channel.classification == "portal"
        assert channel.is_portal

    def test_query_count_is_constant(self):
        """The roster must not cost a query per channel"""
        for index in range(1):
            self.make_channel("one%d@fbi.gov" % index, blocked=1)
        with self.assertNumQueries(agency_channels.__query_count__):
            agency_channels(self.agency)

        big = AgencyFactory(email=None, fax=None)
        for index in range(20):
            address = EmailAddressFactory(
                email="many%d@fbi.gov" % index, status="error"
            )
            AgencyEmailFactory(agency=big, email=address)
            FOIARequestFactory(agency=big, email=address, status="ack")
        with self.assertNumQueries(agency_channels.__query_count__):
            agency_channels(big)


class TestAgencyRollup(TestCase):
    """The agency level scorecard"""

    def setUp(self):
        self.agency = AgencyFactory(email=None, fax=None)

    def make_channel(self, email, blocked=0, status="error"):
        """Attach an address with some blocked traffic"""
        address = EmailAddressFactory(email=email, status=status)
        AgencyEmailFactory(agency=self.agency, email=address)
        if blocked:
            FOIARequestFactory.create_batch(
                blocked, agency=self.agency, email=address, status="ack"
            )
        return address

    def test_blocked_count_is_never_channel_count(self):
        """22 channels holding 49 requests reports 49, not 22

        Channel count is not an impact signal.  A long roster must not read as
        urgent on its own.
        """
        for index in range(22):
            self.make_channel("chan%d@doe.gov" % index, blocked=0)
        channels = agency_channels(self.agency)
        FOIARequestFactory.create_batch(
            49, agency=self.agency, email=channels[0].address, status="ack"
        )
        rollup = agency_rollup(self.agency)
        assert rollup["channels_known"] == 22
        assert rollup["total_blocked"] == 49

    def test_roster_shape_counts(self):
        """Known, broken and active are three different numbers"""
        self.make_channel("broken_active@fbi.gov", blocked=4, status="error")
        self.make_channel("broken_quiet@fbi.gov", blocked=0, status="error")
        self.make_channel("healthy@fbi.gov", blocked=0, status="good")
        rollup = agency_rollup(self.agency)
        assert rollup["channels_known"] == 3
        assert rollup["channels_broken"] == 2
        assert rollup["channels_active"] == 1
        assert rollup["total_blocked"] == 4

    def test_last_success_across_any_channel(self):
        """The most recent confirmed delivery on any of the agency's channels"""
        address = self.make_channel("foia@fbi.gov", blocked=1)
        foia = self.agency.foiarequest_set.first()
        confirmed = timezone.now() - timedelta(days=2)
        comm = EmailCommunicationFactory(
            communication__foia=foia,
            from_email=address,
            confirmed_datetime=confirmed,
        )
        comm.to_emails.set([address])
        rollup = agency_rollup(self.agency)
        assert rollup["last_success"] is not None

    def test_last_success_is_none_without_a_confirmation(self):
        """No confirmed delivery reads as unverified, not as zero"""
        self.make_channel("foia@fbi.gov", blocked=1)
        assert agency_rollup(self.agency)["last_success"] is None

    def test_portal_channels_flag_email_repair_as_wrong(self):
        """A portal roster tells the view that an email swap is the wrong tool"""
        self.make_channel("seattle@mycusthelp.net", blocked=159)
        rollup = agency_rollup(self.agency)
        assert rollup["has_portal_channel"]

    def test_no_portal_channel_by_default(self):
        """An ordinary agency does not flag portal"""
        self.make_channel("foia@fbi.gov", blocked=2)
        assert not agency_rollup(self.agency)["has_portal_channel"]
