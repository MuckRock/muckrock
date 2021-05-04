"""
Tests for the agency importer
"""

# Django
from django.test import TestCase

# Third Party
from nose.tools import assert_greater_equal, assert_not_in, eq_, ok_

# MuckRock
from muckrock.agency.importer import Importer, PyReader
from muckrock.agency.models.communication import AgencyAddress
from muckrock.communication.factories import AddressFactory
from muckrock.core.factories import AgencyFactory, AgencyPhoneFactory
from muckrock.jurisdiction.factories import LocalJurisdictionFactory
from muckrock.portal.models import Portal


class TestAgencyImporter(TestCase):
    """Tests for the mass agency importer"""

    def setUp(self):
        """Create some existing jurisdictions and agencies for the tests"""
        local = LocalJurisdictionFactory()
        state = local.parent
        federal = state.parent
        self.cia = AgencyFactory(
            name="Central Intelligence Agency",
            jurisdiction=federal,
            email=None,
            fax=None,
        )
        self.governor = AgencyFactory(name="Governor's Office", jurisdiction=state,)
        self.police = AgencyFactory(
            name="Boston Police Department", jurisdiction=local,
        )

    def test_match(self):
        """Test different instances of matching existing agencies"""
        reader = PyReader(
            [
                # case insensitive match
                {
                    "agency": "central intelligence agency",
                    "jurisdiction": "united states of america",
                },
                # matches abbrev, fuzzy name match
                {"agency": "Center Intelligence Agency", "jurisdiction": "USA"},
                # matches abbrev
                {"agency": "Governor's Office", "jurisdiction": "MA"},
                # matches state name, fuzzy
                {"agency": "Governors Office", "jurisdiction": "Massachusetts"},
                # local jurisdiction matches
                {"agency": "Boston Police Department", "jurisdiction": "Boston, MA"},
                # fuzzy match, full state name
                {
                    "agency": "The Police Department",
                    "jurisdiction": "Boston, Massachusetts",
                },
                # bad jurisdiction
                {"agency": "The Police Department", "jurisdiction": "Springfield, ZZ"},
                # bad agency
                {"agency": "Sheriff's Secret Police", "jurisdiction": "Boston, MA"},
                # blank agency
                {"agency": "", "jurisdiction": "Boston, MA"},
                # missing agency
                {"jurisdiction": "Boston, MA"},
                # missing agency, blank jurisdiction
                {"jurisdiction": ""},
            ]
        )
        importer = Importer(reader)
        data = list(importer.match())

        eq_(data[0]["match_agency"], self.cia)
        eq_(data[0]["agency_status"], "exact match")

        eq_(data[1]["match_agency"], self.cia)
        assert_greater_equal(data[1]["match_agency_score"], 83)
        eq_(data[1]["agency_status"], "fuzzy match")

        eq_(data[2]["match_agency"], self.governor)
        eq_(data[2]["agency_status"], "exact match")

        eq_(data[3]["match_agency"], self.governor)
        assert_greater_equal(data[3]["match_agency_score"], 83)
        eq_(data[3]["agency_status"], "fuzzy match")

        eq_(data[4]["match_agency"], self.police)
        eq_(data[4]["agency_status"], "exact match")

        eq_(data[5]["match_agency"], self.police)
        assert_greater_equal(data[5]["match_agency_score"], 83)
        eq_(data[5]["agency_status"], "fuzzy match")

        assert_not_in("match_agency", data[6])
        eq_(data[6]["jurisdiction_status"], "no jurisdiction")

        assert_not_in("match_agency", data[7])
        eq_(data[7]["agency_status"], "no agency")

        eq_("missing agency", data[8]["agency_status"])
        eq_("missing agency", data[9]["agency_status"])
        eq_("missing agency", data[10]["agency_status"])
        eq_("missing jurisdiction", data[10]["jurisdiction_status"])

    def test_import_update(self):
        """An import test where we are updating the contact information for an
        existing agency
        """
        reader = PyReader(
            [
                {
                    "agency": "central intelligence agency",
                    "jurisdiction": "united states of america",
                    "email": "foia@cia.gov",
                    "fax": "617-555-0001",
                    "phone": "617-555-0000",
                    "address_city": "Washington",
                    "address_state": "DC",
                    "address_zip": "20505",
                    "portal_url": "https://www.cia.gov/portal/",
                    "portal_type": "foiaonline",
                    "aliases": "CIA",
                    "foia_website": "https://www.cia.gov/foia/",
                    "website": "https://www.cia.gov/",
                },
            ]
        )
        importer = Importer(reader)
        data = list(importer.import_())

        self.cia.refresh_from_db()

        eq_(data[0]["agency_status"], "exact match")

        eq_(self.cia.email.email, "foia@cia.gov")
        eq_(data[0]["email_status"], "set primary")

        eq_(self.cia.fax.number, "+1 617-555-0001")
        eq_(data[0]["fax_status"], "set primary")

        ok_(self.cia.get_phones().filter(number="+1 617-555-0000").exists())
        eq_(data[0]["phone_status"], "set")

        eq_(self.cia.address.zip_code, "20505")
        eq_(self.cia.address.city, "Washington")
        eq_(self.cia.address.state, "DC")
        eq_(data[0]["address_status"], "set primary")

        eq_(self.cia.portal.url, "https://www.cia.gov/portal/")
        eq_(self.cia.portal.type, "foiaonline")
        eq_(data[0]["portal_status"], "set")

        eq_(self.cia.aliases, "CIA")
        eq_(data[0]["aliases_status"], "set")
        eq_(self.cia.url, "https://www.cia.gov/foia/")
        eq_(data[0]["foia_website_status"], "set")
        eq_(self.cia.website, "https://www.cia.gov/")
        eq_(data[0]["website_status"], "set")

    def test_import_update_invalid(self):
        """Test import with some invalid data"""
        reader = PyReader(
            [
                {
                    "agency": "central intelligence agency",
                    "jurisdiction": "united states of america",
                    "email": "foia@cia",
                    "fax": "617-555-001",
                    "phone": "foobar",
                    "address_city": "Washington",
                    "address_state": "foobar",
                    "address_zip": "0123",
                    "portal_url": "not a url",
                    "portal_type": "not a portal",
                    "foia_website": "www.cia.gov/foia/",
                    "website": "foo.bar",
                },
            ]
        )
        importer = Importer(reader)
        data = list(importer.import_())

        eq_(data[0]["agency_status"], "exact match")

        eq_(data[0]["email_status"], "error")
        eq_(data[0]["fax_status"], "error")
        eq_(data[0]["phone_status"], "error")
        eq_(data[0]["address_status"], "error")
        eq_(data[0]["portal_status"], "error")
        eq_(data[0]["foia_website_status"], "error")
        eq_(data[0]["website_status"], "error")

    def test_import_update_duplicate(self):
        """Test an import with data already on the agency"""
        agency_phone = AgencyPhoneFactory(agency=self.police)
        reader = PyReader(
            [
                {
                    "agency": "Boston Police Department",
                    "jurisdiction": "Boston, MA",
                    "email": self.police.email.email,
                    "fax": self.police.fax.number.as_national,
                    "phone": agency_phone.phone.number.as_national,
                },
            ]
        )
        importer = Importer(reader)
        data = list(importer.import_())

        eq_(data[0]["email_status"], "already set")
        eq_(data[0]["fax_status"], "already set")
        eq_(data[0]["phone_status"], "already set")

    def test_import_update_redundant(self):
        """Test an update with data different from the data already on the agency"""
        AgencyAddress.objects.create(
            agency=self.police, address=AddressFactory(), request_type="primary",
        )
        self.police.portal = Portal.objects.create(
            url="https://www.example.com", name="Test Portal", type="other",
        )
        self.police.save()
        reader = PyReader(
            [
                {
                    "agency": "Boston Police Department",
                    "jurisdiction": "Boston, MA",
                    "email": "other@example.com",
                    "cc_emails": "foia1@example.com, foia2@example.com",
                    "fax": "617-555-0001",
                    "address_city": "Washington",
                    "address_state": "DC",
                    "address_zip": "01233",
                    "portal_url": "https://www.cia.gov/portal/",
                    "portal_type": "foiaonline",
                },
            ]
        )
        importer = Importer(reader)
        data = list(importer.import_())

        eq_(data[0]["email_status"], "set other")
        ok_(self.police.emails.filter(email="other@example.com").exists())
        ok_(self.police.emails.filter(email="foia1@example.com").exists())
        ok_(self.police.emails.filter(email="foia2@example.com").exists())
        eq_(data[0]["fax_status"], "set other")
        ok_(self.police.phones.filter(number="617-555-0001").exists())
        eq_(data[0]["address_status"], "set other")
        ok_(self.police.addresses.filter(city="Washington").exists())
        eq_(data[0]["portal_status"], "not set, existing")
        eq_(self.police.portal.name, "Test Portal")

    def test_create(self):
        """Test creating a new agency"""
        reader = PyReader(
            [
                {
                    "agency": "Foobar",
                    "jurisdiction": "united states of america",
                    "email": "foia@new.agency.gov",
                    "cc_emails": "foia1@new.agency.gov, foia2@new.agency.gov",
                    "fax": "617-555-0001",
                    "phone": "617-555-0000",
                    "address_street": "123 Main St",
                    "address_city": "Washington",
                    "address_state": "DC",
                    "address_zip": "20505",
                    "portal_url": "https://www.new-agency.gov/portal/",
                    "portal_type": "nextrequest",
                    "foia_website": "https://www.new-agency.gov/foia/",
                    "website": "https://www.new-agency.gov/",
                    "requires_proxy": "true",
                },
            ]
        )
        importer = Importer(reader)
        data = list(importer.import_())

        eq_(data[0]["agency_status"], "created")
        agency = data[0]["match_agency"]
        eq_(agency.name, "Foobar")

        eq_(agency.email.email, "foia@new.agency.gov")
        eq_(
            sorted(
                e.email
                for e in agency.get_emails(request_type="primary", email_type="cc")
            ),
            ["foia1@new.agency.gov", "foia2@new.agency.gov"],
        )
        eq_(data[0]["email_status"], "set primary")

        eq_(agency.fax.number, "+1 617-555-0001")
        eq_(data[0]["fax_status"], "set primary")

        ok_(agency.get_phones().filter(number="+1 617-555-0000").exists())
        eq_(data[0]["phone_status"], "set")

        eq_(agency.address.street, "123 Main St")
        eq_(agency.address.zip_code, "20505")
        eq_(agency.address.city, "Washington")
        eq_(agency.address.state, "DC")
        eq_(data[0]["address_status"], "set primary")

        eq_(agency.portal.url, "https://www.new-agency.gov/portal/")
        eq_(agency.portal.type, "nextrequest")
        eq_(data[0]["portal_status"], "set")

        assert_not_in("aliases_status", data[0])
        eq_(agency.url, "https://www.new-agency.gov/foia/")
        eq_(data[0]["foia_website_status"], "set")
        eq_(agency.website, "https://www.new-agency.gov/")
        eq_(data[0]["website_status"], "set")

        ok_(agency.requires_proxy)
        eq_(data[0]["requires_proxy_status"], "set true")

    def test_create_minimal(self):
        """Test a creation with minimal contact information supplied"""
        reader = PyReader(
            [{"agency": "Foobar", "jurisdiction": "united states of america",},]
        )
        importer = Importer(reader)
        data = list(importer.import_())

        eq_(data[0]["agency_status"], "created")
        agency = data[0]["match_agency"]
        eq_(agency.name, "Foobar")

    def test_create_bad_jurisdiction(self):
        """Test creating an agency in a bad jurisdiction"""
        reader = PyReader([{"agency": "Foobar", "jurisdiction": "Foobar",},])
        importer = Importer(reader)
        data = list(importer.import_())

        eq_(data[0]["jurisdiction_status"], "no jurisdiction")
        assert_not_in("agency_status", data[0])
