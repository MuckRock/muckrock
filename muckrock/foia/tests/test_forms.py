"""
Form tests for the FOIA application
"""

# Django
from django.contrib.auth.models import AnonymousUser, User
from django.core.urlresolvers import reverse
from django.test import RequestFactory, TestCase

# Third Party
from nose.tools import eq_, ok_

# MuckRock
from muckrock.factories import AgencyFactory, UserFactory
from muckrock.foia.forms import RequestForm
from muckrock.jurisdiction.factories import (
    FederalJurisdictionFactory,
    LocalJurisdictionFactory,
    StateJurisdictionFactory,
)
from muckrock.test_utils import mock_middleware


class TestRequestForm(TestCase):
    """Test the Request Form"""

    def test_get_jurisdiction(self):
        """Test get_jurisdiction"""
        usa = FederalJurisdictionFactory()
        mass = StateJurisdictionFactory(parent=usa)
        boston = LocalJurisdictionFactory(parent=mass)
        form = RequestForm()
        form.cleaned_data = {}

        form.cleaned_data['jurisdiction'] = 'f'
        eq_(form.get_jurisdiction(), usa)

        form.cleaned_data['jurisdiction'] = 's'
        eq_(form.get_jurisdiction(), None)
        form.cleaned_data['state'] = mass
        eq_(form.get_jurisdiction(), mass)

        form.cleaned_data['jurisdiction'] = 'l'
        eq_(form.get_jurisdiction(), None)
        form.cleaned_data['local'] = boston
        eq_(form.get_jurisdiction(), boston)

    def test_get_agency(self):
        """Test get_agency"""
        url = reverse('foia-create')
        factory = RequestFactory()
        usa = FederalJurisdictionFactory(name='USA')
        fbi = AgencyFactory(name='FBI', jurisdiction=usa)
        white_house = AgencyFactory(name='White House', exempt=True)
        user = UserFactory()

        # the user selects an agency
        request = factory.post(url, {'agency-autocomplete': ''})
        request.user = user
        form = RequestForm(request=request)
        form.cleaned_data = {'agency': fbi}
        eq_(form.get_agency(), fbi)

        # the user types the exact name of an agency without selecting it
        request = factory.post(url, {'agency-autocomplete': 'fbi'})
        request.user = user
        form = RequestForm(request=request)
        form.cleaned_data = {'agency': None}
        form.jurisdiction = usa
        eq_(form.get_agency(), fbi)

        # the user creates a new agency
        request = factory.post(url, {'agency-autocomplete': 'cia'})
        request.user = user
        form = RequestForm(request=request)
        form.cleaned_data = {'agency': None}
        form.jurisdiction = usa
        agency = form.get_agency()
        eq_(agency.name, 'cia')
        eq_(agency.newagencytask_set.count(), 1)

        # the user submits no agency or name
        request = factory.post(url, {'agency-autocomplete': ''})
        request.user = user
        form = RequestForm(request=request)
        form.cleaned_data = {'agency': None}
        eq_(form.get_agency(), None)
        ok_(form.has_error('agency'))

        # exempt agency
        request = factory.post(url, {'agency-autocomplete': ''})
        request.user = user
        form = RequestForm(request=request)
        form.cleaned_data = {'agency': white_house}
        eq_(form.get_agency(), None)
        ok_(form.has_error('agency'))

    def test_make_user(self):
        """Test make_user"""
        url = reverse('foia-create')
        factory = RequestFactory()
        request = factory.post(url)
        request = mock_middleware(request)
        request.user = AnonymousUser
        form = RequestForm(request=request)
        form.make_user({
            'full_name': 'John Smith',
            'email': 'john@example.com',
            'newsletter': False,
        })
        ok_(User.objects.filter(email='john@example.com').exists())
