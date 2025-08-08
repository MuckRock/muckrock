"""
Tests for the agency importer
"""

# Django
from django.test import TestCase

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
        self.governor = AgencyFactory(
            name="Governor's Office",
            jurisdiction=state,
        )
        self.police = AgencyFactory(
            name="Boston Police Department",
            jurisdiction=local,
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

        assert data[0]["match_agency"] == self.cia
        assert data[0]["agency_status"] == "exact match"

        assert data[1]["match_agency"] == self.cia
        assert data[1]["match_agency_score"] >= 83
        assert data[1]["agency_status"] == "fuzzy match"

        assert data[2]["match_agency"] == self.governor
        assert data[2]["agency_status"] == "exact match"

        assert data[3]["match_agency"] == self.governor
        assert data[3]["match_agency_score"] >= 83
        assert data[3]["agency_status"] == "fuzzy match"

        assert data[4]["match_agency"] == self.police
        assert data[4]["agency_status"] == "exact match"

        assert data[5]["match_agency"] == self.police
        assert data[5]["match_agency_score"] >= 83
        assert data[5]["agency_status"] == "fuzzy match"

        assert "match_agency" not in data[6]
        assert data[6]["jurisdiction_status"] == "no jurisdiction"

        assert "match_agency" not in data[7]
        assert data[7]["agency_status"] == "no agency"

        assert "missing agency" == data[8]["agency_status"]
        assert "missing agency" == data[9]["agency_status"]
        assert "missing agency" == data[10]["agency_status"]
        assert "missing jurisdiction" == data[10]["jurisdiction_status"]

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
                }
            ]
        )
        importer = Importer(reader)
        data = list(importer.import_())

        self.cia.refresh_from_db()

        assert data[0]["agency_status"] == "exact match"

        assert self.cia.email.email == "foia@cia.gov"
        assert data[0]["email_status"] == "set primary"

        assert self.cia.fax.number == "+1 617-555-0001"
        assert data[0]["fax_status"] == "set primary"

        assert self.cia.get_phones().filter(number="+1 617-555-0000").exists()
        assert data[0]["phone_status"] == "set"

        assert self.cia.address.zip_code == "20505"
        assert self.cia.address.city == "Washington"
        assert self.cia.address.state == "DC"
        assert data[0]["address_status"] == "set primary"

        assert self.cia.portal.url == "https://www.cia.gov/portal/"
        assert self.cia.portal.type == "foiaonline"
        assert data[0]["portal_status"] == "set"

        assert self.cia.aliases == "CIA"
        assert data[0]["aliases_status"] == "set"
        assert self.cia.url == "https://www.cia.gov/foia/"
        assert data[0]["foia_website_status"] == "set"
        assert self.cia.website == "https://www.cia.gov/"
        assert data[0]["website_status"] == "set"

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

        assert data[0]["agency_status"] == "exact match"

        assert data[0]["email_status"] == "error"
        assert data[0]["fax_status"] == "error"
        assert data[0]["phone_status"] == "error"
        assert data[0]["address_status"] == "error"
        assert data[0]["portal_status"] == "error"
        assert data[0]["foia_website_status"] == "error"
        assert data[0]["website_status"] == "error"

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
                }
            ]
        )
        importer = Importer(reader)
        data = list(importer.import_())

        assert data[0]["email_status"] == "already set"
        assert data[0]["fax_status"] == "already set"
        assert data[0]["phone_status"] == "already set"

    def test_import_update_redundant(self):
        """Test an update with data different from the data already on the agency"""
        AgencyAddress.objects.create(
            agency=self.police,
            address=AddressFactory(),
            request_type="primary",
        )
        self.police.portal = Portal.objects.create(
            url="https://www.example.com",
            name="Test Portal",
            type="other",
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

        assert data[0]["email_status"] == "set other"
        assert self.police.emails.filter(email="other@example.com").exists()
        assert self.police.emails.filter(email="foia1@example.com").exists()
        assert self.police.emails.filter(email="foia2@example.com").exists()
        assert data[0]["fax_status"] == "set other"
        assert self.police.phones.filter(number="617-555-0001").exists()
        assert data[0]["address_status"] == "set other"
        assert self.police.addresses.filter(city="Washington").exists()
        assert data[0]["portal_status"] == "not set, existing"
        assert self.police.portal.name == "Test Portal"

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

        assert data[0]["agency_status"] == "created"
        agency = data[0]["match_agency"]
        assert agency.name == "Foobar"

        assert agency.email.email == "foia@new.agency.gov"
        assert sorted(
            e.email for e in agency.get_emails(request_type="primary", email_type="cc")
        ) == ["foia1@new.agency.gov", "foia2@new.agency.gov"]
        assert data[0]["email_status"] == "set primary"

        assert agency.fax.number == "+1 617-555-0001"
        assert data[0]["fax_status"] == "set primary"

        assert agency.get_phones().filter(number="+1 617-555-0000").exists()
        assert data[0]["phone_status"] == "set"

        assert agency.address.street == "123 Main St"
        assert agency.address.zip_code == "20505"
        assert agency.address.city == "Washington"
        assert agency.address.state == "DC"
        assert data[0]["address_status"] == "set primary"

        assert agency.portal.url == "https://www.new-agency.gov/portal/"
        assert agency.portal.type == "nextrequest"
        assert data[0]["portal_status"] == "set"

        assert "aliases_status" not in data[0]
        assert agency.url == "https://www.new-agency.gov/foia/"
        assert data[0]["foia_website_status"] == "set"
        assert agency.website == "https://www.new-agency.gov/"
        assert data[0]["website_status"] == "set"

        assert agency.requires_proxy
        assert data[0]["requires_proxy_status"] == "set true"

    def test_create_minimal(self):
        """Test a creation with minimal contact information supplied"""
        reader = PyReader(
            [{"agency": "Foobar", "jurisdiction": "united states of america"}]
        )
        importer = Importer(reader)
        data = list(importer.import_())

        assert data[0]["agency_status"] == "created"
        agency = data[0]["match_agency"]
        assert agency.name == "Foobar"

    def test_create_bad_jurisdiction(self):
        """Test creating an agency in a bad jurisdiction"""
        reader = PyReader([{"agency": "Foobar", "jurisdiction": "Foobar"}])
        importer = Importer(reader)
        data = list(importer.import_())

        assert data[0]["jurisdiction_status"] == "no jurisdiction"
        assert "agency_status" not in data[0]
