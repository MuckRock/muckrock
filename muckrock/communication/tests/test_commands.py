# -*- coding: utf-8 -*-
"""
Tests for the communication app's management commands
"""

# Django
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

# Standard Library
from io import StringIO

# MuckRock
from muckrock.communication.factories import (
    EmailAddressFactory,
    EmailCommunicationFactory,
)
from muckrock.communication.models import EmailAddress, EmailError, EmailOpen, Source
from muckrock.core.factories import AgencyEmailFactory, AgencyFactory, UserFactory
from muckrock.crowdsource.factories import CrowdsourceFactory
from muckrock.foia.factories import FOIARequestFactory


def make_variants(*emails):
    """Create rows carrying mixed case, bypassing the model's normalization

    EmailAddress.save() lowercases the address, so these rows cannot be built
    through the factory or save().  bulk_create skips save(), which is exactly
    how the pre-normalization rows we need to merge got into the database.
    """
    return EmailAddress.objects.bulk_create(
        [EmailAddress(email=email) for email in emails]
    )


class TestMergeEmailAddresses(TestCase):
    """Test the merge_email_addresses command"""

    def call(self, *args):
        """Run the command, returning its stdout"""
        out = StringIO()
        call_command("merge_email_addresses", *args, stdout=out)
        return out.getvalue()

    def test_merges_case_variants(self):
        """Three rows differing only by case collapse to one

        Nothing references any of them, so the pk tie-break decides.  The
        survivor comes out lowercased whatever spelling it went in with --
        save() does that, so the command needs no canonical-spelling rule.
        """
        first, second, third = make_variants(
            "FOIPAQUESTIONS@fbi.gov",
            "foipaquestions@fbi.gov",
            "FOIPAQuestions@fbi.gov",
        )
        self.call()
        assert EmailAddress.objects.filter(pk__in=[second.pk, third.pk]).count() == 0
        first.refresh_from_db()
        assert first.email == "foipaquestions@fbi.gov"

    def test_survivor_is_lowercased_when_no_member_is(self):
        """A group with no lowercase member still ends up normalized"""
        first, second = make_variants("MIXED@fbi.gov", "Mixed@fbi.gov")
        self.call()
        assert EmailAddress.objects.filter(pk=second.pk).count() == 0
        first.refresh_from_db()
        assert first.email == "mixed@fbi.gov"

    def test_most_referenced_row_survives(self):
        """The row the most rows already point at is the canonical one

        Reference count measures how established a row actually is, where pk
        age only proxies for it.  Keeping the heaviest row also means the
        fewest references have to move, which shrinks the transaction and the
        surface where a PROTECT failure can bite.
        """
        first, second, third = make_variants("Aa@fbi.gov", "aa@fbi.gov", "aA@fbi.gov")
        FOIARequestFactory.create_batch(2, email=first)
        FOIARequestFactory.create_batch(5, email=second)
        FOIARequestFactory.create_batch(1, email=third)
        self.call()
        assert EmailAddress.objects.filter(pk__in=[first.pk, third.pk]).count() == 0
        second.refresh_from_db()
        assert second.email == "aa@fbi.gov"

    def test_blocked_requests_sum_onto_survivor(self):
        """Requests routed at any variant end up on the surviving row"""
        first, second, third = make_variants("Ba@fbi.gov", "ba@fbi.gov", "bA@fbi.gov")
        FOIARequestFactory.create_batch(2, email=first)
        FOIARequestFactory.create_batch(5, email=second)
        FOIARequestFactory.create_batch(1, email=third)
        self.call()
        second.refresh_from_db()
        assert second.foias.count() == 8

    def test_references_are_counted_across_relation_types(self):
        """A row's weight is every kind of reference, not just requests

        Two agency links plus an error and an open outweigh three requests, so
        the rubric cannot just look at the relation that is easiest to count.
        """
        light, heavy = make_variants("Ca@fbi.gov", "ca@fbi.gov")
        FOIARequestFactory.create_batch(3, email=light)
        AgencyEmailFactory(agency=AgencyFactory(), email=heavy)
        AgencyEmailFactory(agency=AgencyFactory(), email=heavy)
        comm = EmailCommunicationFactory()
        EmailError.objects.create(
            email=comm,
            datetime=timezone.now(),
            recipient=heavy,
            code="550",
            error="no such mailbox",
            event="failed",
            reason="bounce",
        )
        EmailOpen.objects.create(
            email=comm, datetime=timezone.now(), event="opened", recipient=heavy
        )
        self.call()
        assert EmailAddress.objects.filter(pk=light.pk).count() == 0
        heavy.refresh_from_db()
        assert heavy.email == "ca@fbi.gov"

    def test_ties_break_on_lowest_pk(self):
        """Equal weight falls back to the oldest row, deterministically

        Pinned so the canonical choice never depends on row ordering, which
        would make a dry-run report stop predicting the real run.
        """
        first, second = make_variants("Da@fbi.gov", "da@fbi.gov")
        FOIARequestFactory.create_batch(2, email=first)
        FOIARequestFactory.create_batch(2, email=second)
        self.call()
        assert EmailAddress.objects.filter(pk=second.pk).count() == 0
        first.refresh_from_db()
        assert first.email == "da@fbi.gov"

    def test_unreferenced_group_falls_back_to_lowest_pk(self):
        """With nothing pointing anywhere, the oldest row wins"""
        first, second = make_variants("Ea@fbi.gov", "ea@fbi.gov")
        self.call()
        assert EmailAddress.objects.filter(pk=second.pk).count() == 0
        assert EmailAddress.objects.filter(pk=first.pk).exists()

    def test_report_names_the_weight_behind_the_choice(self):
        """The dry-run report has to say why a row was kept

        The report is the review artifact; a bare "keeping pk=N" is not
        reviewable without the number that drove it.
        """
        light, heavy = make_variants("Fa@fbi.gov", "fa@fbi.gov")
        FOIARequestFactory.create_batch(1, email=light)
        FOIARequestFactory.create_batch(4, email=heavy)
        output = self.call("--dry-run")
        assert "4 reference" in output

    def test_error_status_wins(self):
        """A mailbox that bounces under one spelling bounces under all"""
        upper, lower = make_variants("B@fbi.gov", "b@fbi.gov")
        EmailAddress.objects.filter(pk=upper.pk).update(status="good")
        EmailAddress.objects.filter(pk=lower.pk).update(status="error")
        self.call()
        upper.refresh_from_db()
        assert upper.status == "error"

    def test_name_takes_the_surviving_rows_name_when_it_has_one(self):
        """The surviving row's own name wins"""
        upper, lower = make_variants("C@fbi.gov", "c@fbi.gov")
        EmailAddress.objects.filter(pk=upper.pk).update(name="Survivor")
        EmailAddress.objects.filter(pk=lower.pk).update(name="Other")
        self.call()
        upper.refresh_from_db()
        assert upper.name == "Survivor"

    def test_name_falls_back_to_variant(self):
        """A blank canonical name takes the first non-blank variant name"""
        upper, lower = make_variants("D@fbi.gov", "d@fbi.gov")
        EmailAddress.objects.filter(pk=upper.pk).update(name="")
        EmailAddress.objects.filter(pk=lower.pk).update(name="Fallback")
        self.call()
        upper.refresh_from_db()
        assert upper.name == "Fallback"

    def test_agency_email_links_collapse(self):
        """Duplicate (agency, email) links collapse, most specific kept"""
        upper, lower = make_variants("E@fbi.gov", "e@fbi.gov")
        agency = AgencyFactory()
        AgencyEmailFactory(
            agency=agency, email=upper, request_type="none", email_type="none"
        )
        AgencyEmailFactory(
            agency=agency, email=lower, request_type="primary", email_type="to"
        )
        self.call()
        links = agency.agencyemail_set.filter(email=upper)
        assert links.count() == 1
        link = links.get()
        assert link.request_type == "primary"
        assert link.email_type == "to"

    def test_m2m_repoints_dedupe(self):
        """A communication holding two variants ends with one entry"""
        upper, lower = make_variants("F@fbi.gov", "f@fbi.gov")
        comm = EmailCommunicationFactory()
        comm.to_emails.set([upper, lower])
        comm.cc_emails.set([upper, lower])
        self.call()
        assert list(comm.to_emails.all()) == [upper]
        assert list(comm.cc_emails.all()) == [upper]

    def test_protected_relations_repoint(self):
        """Error, open, source and from_email rows all move to the survivor"""
        upper, lower = make_variants("G@fbi.gov", "g@fbi.gov")
        # Weight the survivor deliberately, so the protected rows below sit on
        # the losing row and genuinely have to move.
        FOIARequestFactory.create_batch(9, email=upper)
        comm = EmailCommunicationFactory(from_email=lower)
        EmailError.objects.create(
            email=comm,
            datetime=timezone.now(),
            recipient=lower,
            code="550",
            error="mailbox unavailable",
            event="failed",
            reason="bounce",
        )
        EmailOpen.objects.create(
            email=comm, datetime=timezone.now(), event="opened", recipient=lower
        )
        Source.objects.create(
            datetime=timezone.now(),
            user=UserFactory(),
            type="user",
            email_address=lower,
        )
        self.call()
        comm.refresh_from_db()
        assert comm.from_email == upper
        assert upper.errors.count() == 1
        assert upper.opens.count() == 1
        assert upper.sources.count() == 1

    def test_foia_cc_emails_repoint_and_dedupe(self):
        """A request cc'ing two variants ends with one"""
        upper, lower = make_variants("H@fbi.gov", "h@fbi.gov")
        foia = FOIARequestFactory()
        foia.cc_emails.set([upper, lower])
        self.call()
        assert list(foia.cc_emails.all()) == [upper]

    def test_crowdsource_submission_emails_repoint(self):
        """Crowdsource submission emails move to the survivor"""
        upper, lower = make_variants("I@fbi.gov", "i@fbi.gov")
        crowdsource = CrowdsourceFactory()
        crowdsource.submission_emails.set([upper, lower])
        self.call()
        assert list(crowdsource.submission_emails.all()) == [upper]

    def test_dry_run_writes_nothing(self):
        """--dry-run reports the same groups and changes no rows"""
        make_variants("Jj@fbi.gov", "jj@fbi.gov", "jJ@fbi.gov")
        before = set(EmailAddress.objects.values_list("pk", "email", "status", "name"))
        output = self.call("--dry-run")
        after = set(EmailAddress.objects.values_list("pk", "email", "status", "name"))
        assert before == after
        assert "jj@fbi.gov" in output

    def test_rerun_is_a_noop(self):
        """Running again after a successful merge changes nothing"""
        make_variants("K@fbi.gov", "k@fbi.gov")
        self.call()
        before = set(EmailAddress.objects.values_list("pk", "email", "status", "name"))
        self.call()
        after = set(EmailAddress.objects.values_list("pk", "email", "status", "name"))
        assert before == after

    def test_non_colliding_rows_are_lowercased_but_kept(self):
        """A row with no collision survives, lowercased"""
        (only,) = make_variants("Lonely@fbi.gov")
        self.call()
        only.refresh_from_db()
        assert only.email == "lonely@fbi.gov"
        assert EmailAddress.objects.filter(pk=only.pk).exists()

    def test_already_lowercase_untouched(self):
        """An already normalized row is left completely alone"""
        address = EmailAddressFactory(email="fine@fbi.gov", name="Fine")
        self.call()
        address.refresh_from_db()
        assert address.email == "fine@fbi.gov"
        assert address.name == "Fine"
