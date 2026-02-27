"""
Tests for NFOICPartner model and prompt injection
"""
# Third Party
import pytest
from django.test import TestCase

# Local
from apps.jurisdiction import factories
from apps.jurisdiction.models import NFOICPartner
from apps.jurisdiction.services.providers.helpers import get_nfoic_partner_for_prompt


class TestNFOICPartnerModel(TestCase):
    """Tests for NFOICPartner model"""

    def test_create_partner(self):
        """Test creating an NFOICPartner"""
        partner = factories.NFOICPartnerFactory(
            jurisdiction_abbrev='CO',
            name='Colorado Freedom of Information Coalition',
        )

        assert partner.id is not None
        assert partner.jurisdiction_abbrev == 'CO'
        assert partner.name == 'Colorado Freedom of Information Coalition'
        assert partner.is_active is True

    def test_str(self):
        """Test __str__ representation"""
        partner = factories.NFOICPartnerFactory(
            jurisdiction_abbrev='GA',
            name='Georgia First Amendment Foundation',
        )
        assert str(partner) == '[GA] Georgia First Amendment Foundation'

    def test_ordering(self):
        """Test default ordering by jurisdiction_abbrev, order, name"""
        factories.NFOICPartnerFactory(
            jurisdiction_abbrev='GA', order=1, name='Beta Org'
        )
        factories.NFOICPartnerFactory(
            jurisdiction_abbrev='CO', order=0, name='Alpha Org'
        )
        factories.NFOICPartnerFactory(
            jurisdiction_abbrev='GA', order=0, name='Alpha Org'
        )

        partners = list(NFOICPartner.objects.values_list('jurisdiction_abbrev', 'name'))
        assert partners == [
            ('CO', 'Alpha Org'),
            ('GA', 'Alpha Org'),
            ('GA', 'Beta Org'),
        ]


class TestGetNFOICPartnerForPrompt(TestCase):
    """Tests for get_nfoic_partner_for_prompt helper"""

    def test_empty_state_returns_empty(self):
        """No state provided returns empty string"""
        assert get_nfoic_partner_for_prompt(None) == ""
        assert get_nfoic_partner_for_prompt("") == ""

    def test_no_partners_returns_empty(self):
        """State with no partners returns empty string"""
        assert get_nfoic_partner_for_prompt("ZZ") == ""

    def test_formatted_output(self):
        """Test formatted output includes partner details"""
        factories.NFOICPartnerFactory(
            jurisdiction_abbrev='CO',
            name='CO FOI Coalition',
            website='https://cofoic.org',
            email='info@cofoic.org',
            phone='303-555-1234',
            description='Colorado FOI advocacy',
        )

        result = get_nfoic_partner_for_prompt('CO')

        assert 'STATE FOI ADVOCACY RESOURCES:' in result
        assert 'CO FOI Coalition' in result
        assert 'https://cofoic.org' in result
        assert 'info@cofoic.org' in result
        assert '303-555-1234' in result
        assert 'Colorado FOI advocacy' in result

    def test_inactive_excluded(self):
        """Inactive partners are excluded from prompt"""
        factories.NFOICPartnerFactory(
            jurisdiction_abbrev='CO',
            name='Active Org',
            is_active=True,
        )
        factories.NFOICPartnerFactory(
            jurisdiction_abbrev='CO',
            name='Inactive Org',
            is_active=False,
        )

        result = get_nfoic_partner_for_prompt('CO')

        assert 'Active Org' in result
        assert 'Inactive Org' not in result

    def test_state_filtering(self):
        """Only partners for the requested state are included"""
        factories.NFOICPartnerFactory(
            jurisdiction_abbrev='CO',
            name='Colorado Org',
        )
        factories.NFOICPartnerFactory(
            jurisdiction_abbrev='GA',
            name='Georgia Org',
        )

        result = get_nfoic_partner_for_prompt('CO')

        assert 'Colorado Org' in result
        assert 'Georgia Org' not in result

    def test_blank_fields_omitted(self):
        """Blank optional fields are not included in output"""
        factories.NFOICPartnerFactory(
            jurisdiction_abbrev='CO',
            name='Minimal Org',
            website='',
            email='',
            phone='',
            description='',
        )

        result = get_nfoic_partner_for_prompt('CO')

        assert 'Minimal Org' in result
        assert 'Website:' not in result
        assert 'Email:' not in result
        assert 'Phone:' not in result
        assert 'Description:' not in result

    def test_multiple_partners(self):
        """Multiple partners for same state are all included"""
        factories.NFOICPartnerFactory(
            jurisdiction_abbrev='CO',
            name='First Org',
            order=0,
        )
        factories.NFOICPartnerFactory(
            jurisdiction_abbrev='CO',
            name='Second Org',
            order=1,
        )

        result = get_nfoic_partner_for_prompt('CO')

        assert 'First Org' in result
        assert 'Second Org' in result
        # First org should appear before second based on order
        assert result.index('First Org') < result.index('Second Org')
