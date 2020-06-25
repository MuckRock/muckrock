"""
Tests for the agency importer
"""

# Django
from django.test import TestCase

# Third Party
from nose.tools import (
    assert_greater_equal,
    assert_in,
    assert_is_not_none,
    assert_not_in,
    eq_,
    ok_,
)

# MuckRock
from muckrock.agency.importer import Importer, PyReader
from muckrock.agency.models import Agency
from muckrock.communication.factories import (
    EmailAddressFactory,
    PhoneNumberFactory,
)
from muckrock.core.factories import (
    AgencyEmailFactory,
    AgencyFactory,
    AgencyPhoneFactory,
    ProfessionalUserFactory,
    UserFactory,
)
from muckrock.jurisdiction.factories import LocalJurisdictionFactory


class TestAgencyImporter(TestCase):
    def setUp(self):
        local = LocalJurisdictionFactory()
        state = local.parent
        federal = state.parent
        self.cia = AgencyFactory(
            name='Central Intelligence Agency',
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
        reader = PyReader([
            # case insensitive match
            {
                'agency': 'central intelligence agency',
                'jurisdiction': 'united states of america'
            },
            # matches abbrev, fuzzy name match
            {
                'agency': 'Center Intelligence Agency',
                'jurisdiction': 'USA'
            },
            # matches abbrev
            {
                'agency': "Governor's Office",
                'jurisdiction': 'MA'
            },
            # matches state name, fuzzy
            {
                'agency': "Governors Office",
                'jurisdiction': 'Massachusetts'
            },
            # local jurisdiction matches
            {
                'agency': "Boston Police Department",
                'jurisdiction': 'Boston, MA'
            },
            # fuzzy match, full state name
            {
                'agency': "The Police Department",
                'jurisdiction': 'Boston, Massachusetts'
            },
            # bad jurisdiction
            {
                'agency': "The Police Department",
                'jurisdiction': 'Springfield, ZZ'
            },
            # bad agency
            {
                'agency': "Sheriff's Secret Police",
                'jurisdiction': 'Boston, MA'
            },
            # blank agency
            {
                'agency': "",
                'jurisdiction': 'Boston, MA'
            },
            # missing agency
            {
                'jurisdiction': 'Boston, MA'
            },
            # missing agency, blank jurisdiction
            {
                'jurisdiction': ''
            },
        ])
        importer = Importer(reader)
        data = list(importer.match())

        eq_(data[0]['match_agency'], self.cia)
        eq_(data[0]['agency_status'], 'exact match')

        eq_(data[1]['match_agency'], self.cia)
        assert_greater_equal(data[1]['match_agency_score'], 83)
        eq_(data[1]['agency_status'], 'fuzzy match')

        eq_(data[2]['match_agency'], self.governor)
        eq_(data[2]['agency_status'], 'exact match')

        eq_(data[3]['match_agency'], self.governor)
        assert_greater_equal(data[3]['match_agency_score'], 83)
        eq_(data[3]['agency_status'], 'fuzzy match')

        eq_(data[4]['match_agency'], self.police)
        eq_(data[4]['agency_status'], 'exact match')

        eq_(data[5]['match_agency'], self.police)
        assert_greater_equal(data[5]['match_agency_score'], 83)
        eq_(data[5]['agency_status'], 'fuzzy match')

        assert_not_in('match_agency', data[6])
        eq_(data[6]['jurisdiction_status'], 'no jurisdiction')

        assert_not_in('match_agency', data[7])
        eq_(data[7]['agency_status'], 'no agency')

        eq_('missing agency', data[8]['agency_status'])
        eq_('missing agency', data[9]['agency_status'])
        eq_('missing agency', data[10]['agency_status'])
        eq_('missing jurisdiction', data[10]['jurisdiction_status'])

    # update
    #  valid data
    #  invalid data
    #  duplicate data
    #  redundant data
    # create
    #  valid data
    #  invalid data

    def test_import_update(self):
        reader = PyReader([
            {
                'agency': 'central intelligence agency',
                'jurisdiction': 'united states of america',
                'email': 'foia@cia.gov',
                'fax': '555-555-0001',
                'phone': '555-555-0000',
                'address_city': 'Washington',
                'address_state': 'DC',
                'address_zip': '20505',
                'portal_url': 'https://www.cia.gov/portal/',
                'portal_type': 'foiaonline',
                'aliases': 'CIA',
                'foia_website': 'https://www.cia.gov/foia/',
                'website': 'https://www.cia.gov/',
            },
        ])
        importer = Importer(reader)
        data = list(importer.import_())

        self.cia.refresh_from_db()

        eq_(data[0]['agency_status'], 'exact match')

        eq_(self.cia.email.email, 'foia@cia.gov')
        eq_(data[0]['email_status'], 'set primary')

        eq_(self.cia.fax.number, '+1 555-555-0001')
        eq_(data[0]['fax_status'], 'set primary')

        ok_(self.cia.get_phones().filter(number='+1 555-555-0000').exists())
        eq_(data[0]['phone_status'], 'set')

        eq_(self.cia.address.zip_code, '20505')
        eq_(self.cia.address.city, 'Washington')
        eq_(self.cia.address.state, 'DC')
        eq_(data[0]['address_status'], 'set primary')

        eq_(self.cia.portal.url, 'https://www.cia.gov/portal/')
        eq_(self.cia.portal.type, 'foiaonline')
        eq_(data[0]['portal_status'], 'set')

        eq_(self.cia.aliases, 'CIA')
        eq_(data[0]['aliases_status'], 'set')
        eq_(self.cia.url, 'https://www.cia.gov/foia/')
        eq_(data[0]['foia_website_status'], 'set')
        eq_(self.cia.website, 'https://www.cia.gov/')
        eq_(data[0]['website_status'], 'set')

    def test_import_update_invalid(self):
        pass

    def test_import_update_duplicate(self):
        reader = PyReader([
            {
                'agency': 'Boston Police Department',
                'jurisdiction': 'Boston, MA',
                'email': self.police.email.email,
                'fax': self.police.fax.number.as_national,
            },
        ])
        importer = Importer(reader)
        data = list(importer.import_())

        eq_(data[0]['email_status'], 'already set')
        eq_(data[0]['fax_status'], 'already set')

    def test_import_update_redundant(self):
        reader = PyReader([
            {
                'agency': 'Boston Police Department',
                'jurisdiction': 'Boston, MA',
                'email': 'other@example.com',
                'fax': '555-555-0001',
            },
        ])
        importer = Importer(reader)
        data = list(importer.import_())

        eq_(data[0]['email_status'], 'set other')
        ok_(self.police.emails.filter(email='other@example.com').exists())
        eq_(data[0]['fax_status'], 'set other')
        ok_(self.police.phones.filter(number='555-555-0001').exists())

    def test_create(self):
        reader = PyReader([
            {
                'agency': 'Foobar',
                'jurisdiction': 'united states of america',
                'email': 'foia@new.agency.gov',
                'fax': '555-555-0001',
                'phone': '555-555-0000',
                'address_street': '123 Main St',
                'address_city': 'Washington',
                'address_state': 'DC',
                'address_zip': '20505',
                'portal_url': 'https://www.new-agency.gov/portal/',
                'portal_type': 'nextrequest',
                'foia_website': 'https://www.new-agency.gov/foia/',
                'website': 'https://www.new-agency.gov/',
            },
        ])
        importer = Importer(reader)
        data = list(importer.import_())

        eq_(data[0]['agency_status'], 'created')
        agency = data[0]['match_agency']
        eq_(agency.name, 'Foobar')

        eq_(agency.email.email, 'foia@new.agency.gov')
        eq_(data[0]['email_status'], 'set primary')

        eq_(agency.fax.number, '+1 555-555-0001')
        eq_(data[0]['fax_status'], 'set primary')

        ok_(agency.get_phones().filter(number='+1 555-555-0000').exists())
        eq_(data[0]['phone_status'], 'set')

        eq_(agency.address.street, '123 Main St')
        eq_(agency.address.zip_code, '20505')
        eq_(agency.address.city, 'Washington')
        eq_(agency.address.state, 'DC')
        eq_(data[0]['address_status'], 'set primary')

        eq_(agency.portal.url, 'https://www.new-agency.gov/portal/')
        eq_(agency.portal.type, 'nextrequest')
        eq_(data[0]['portal_status'], 'set')

        assert_not_in('aliases_status', data[0])
        eq_(agency.url, 'https://www.new-agency.gov/foia/')
        eq_(data[0]['foia_website_status'], 'set')
        eq_(agency.website, 'https://www.new-agency.gov/')
        eq_(data[0]['website_status'], 'set')

    def test_create_invalid(self):
        pass
