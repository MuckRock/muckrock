# -*- coding: utf-8 -*-
"""
Tests for email address normalization

An email address row stands in for a real mailbox.  RFC 5321 makes the local
part case sensitive in principle, but no provider we deliver to treats it that
way, and our own data shows the case variants are the same mailbox receiving
the same bounces.  These tests pin that decision down.
"""

# Django
from django.forms import ValidationError
from django.test import TestCase

# Third Party
import pytest

# MuckRock
from muckrock.communication.models import EmailAddress, EmailAddressQuerySet


class TestNormalizeEmail(TestCase):
    """Test the _normalize_email helper"""

    def normalize(self, email):
        """Convenience wrapper around the queryset static method"""
        # pylint: disable=protected-access
        return EmailAddressQuerySet._normalize_email(email)

    def test_lowercases_local_part_and_domain(self):
        """Both halves of the address are lowercased"""
        assert self.normalize("FOIPAQuestions@FBI.gov") == "foipaquestions@fbi.gov"

    def test_lowercases_local_part_alone(self):
        """A mixed case local part on an already lowercase domain"""
        assert self.normalize("FOIPAQUESTIONS@fbi.gov") == "foipaquestions@fbi.gov"

    def test_strips_invisible_spaces(self):
        """Zero width spaces are still stripped"""
        assert self.normalize("foia\u200b@example.gov") == "foia@example.gov"

    def test_rejects_invalid(self):
        """Invalid addresses still raise"""
        with pytest.raises(ValidationError):
            self.normalize("foobar")


class TestFetchCollapsesCase(TestCase):
    """Fetching an address by any casing lands on one row"""

    def test_fetch_returns_same_row(self):
        """Two casings of one mailbox fetch the same row"""
        first = EmailAddress.objects.fetch("FOIPAQUESTIONS@fbi.gov")
        second = EmailAddress.objects.fetch("foipaquestions@fbi.gov")
        third = EmailAddress.objects.fetch("FOIPAQuestions@fbi.gov")
        assert first.pk == second.pk == third.pk
        assert (
            EmailAddress.objects.filter(email__iexact="foipaquestions@fbi.gov").count()
            == 1
        )

    def test_fetch_stores_lowercase(self):
        """The stored value is lowercase"""
        assert EmailAddress.objects.fetch("Mixed@Case.gov").email == "mixed@case.gov"

    def test_fetch_many_dedupes_within_one_header(self):
        """Mixed case duplicates in a single header collapse to one address"""
        addresses = EmailAddress.objects.fetch_many(
            "FOIA@agency.gov, foia@agency.gov, other@agency.gov"
        )
        assert len(addresses) == 2
        assert len({a.pk for a in addresses}) == 2
        assert EmailAddress.objects.filter(email__iexact="foia@agency.gov").count() == 1

    def test_save_lowercases_defensively(self):
        """A direct save cannot reintroduce a variant"""
        address = EmailAddress(email="Mixed@Case.gov")
        address.save()
        address.refresh_from_db()
        assert address.email == "mixed@case.gov"

    def test_save_lowercases_on_update(self):
        """Editing an address through the admin cannot reintroduce a variant

        EmailAddressAdmin is a plain ModelForm over a plain EmailField, so
        this is the only thing standing between a staff edit and a second row
        for one mailbox.
        """
        address = EmailAddress.objects.fetch("foia@agency.gov")
        address.email = "FOIA@AGENCY.GOV"
        address.save()
        address.refresh_from_db()
        assert address.email == "foia@agency.gov"

    def test_save_normalizes_a_legacy_row_on_next_touch(self):
        """A pre-merge row is repaired the next time anything saves it

        Rows like this exist until the merge command runs.  Normalizing on
        save means an unrelated touch -- recording a bounce, say -- moves them
        toward one row per mailbox rather than leaving them split.
        """
        (address,) = EmailAddress.objects.bulk_create(
            [EmailAddress(email="Legacy@Case.gov")]
        )
        address.status = "error"
        address.save()
        address.refresh_from_db()
        assert address.email == "legacy@case.gov"
