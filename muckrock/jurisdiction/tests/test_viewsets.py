"""
Test the API viewsets for the Jurisdiction application.
"""

from django.test import TestCase

from nose.tools import eq_, ok_
from rest_framework.test import APIRequestFactory, APIClient, force_authenticate

from muckrock.factories import UserFactory, FOIARequestFactory
from muckrock.jurisdiction.factories import StateJurisdictionFactory, ExemptionFactory
from muckrock.jurisdiction.serializers import ExemptionSerializer
from muckrock.jurisdiction.viewsets import ExemptionViewSet

class TestExemptionList(TestCase):
    """
    The exemption list view allows exemptions to be listed and filtered.
    An exemption can be filtered by jurisdiction or by a keyword query.
    """
    def setUp(self):
        self.endpoint = '/exemption/'
        self.factory = APIRequestFactory()
        self.view = ExemptionViewSet.as_view({'get': 'list'})

    def test_list_all(self):
        """A basic GET request should return all the exemptions."""
        exemption1 = ExemptionFactory(name='Exemption One')
        exemption2 = ExemptionFactory(name='Exemption Two')
        request = self.factory.get(self.endpoint)
        response = self.view(request)
        eq_(response.status_code, 200)
        ok_(ExemptionSerializer(exemption1).data in response.data['results'])
        ok_(ExemptionSerializer(exemption2).data in response.data['results'])

    def test_list_query_filter(self):
        """The list should be filterable by a query."""
        exemption_foo = ExemptionFactory(name='Foo')
        exemption_bar = ExemptionFactory(name='Bar')
        request = self.factory.get(self.endpoint, {'q': 'Foo'})
        response = self.view(request)
        eq_(response.status_code, 200)
        ok_(ExemptionSerializer(exemption_foo).data in response.data['results'],
            'An exemption matching the query should be included in the list.')
        ok_(ExemptionSerializer(exemption_bar).data not in response.data['results'],
            'An exemption not matching the query should not be included in the list.')

    def test_list_jurisdiction_filter(self):
        """The list should be filterable by a jurisdiction."""
        massachusetts = StateJurisdictionFactory(name='Massachusetts', abbrev='MA')
        washington = StateJurisdictionFactory(name='Washington', abbrev='WA')
        exemption_ma = ExemptionFactory(jurisdiction=massachusetts)
        exemption_wa = ExemptionFactory(jurisdiction=washington)
        request = self.factory.get(self.endpoint, {'jurisdiction': massachusetts.pk})
        response = self.view(request)
        eq_(response.status_code, 200)
        ok_(ExemptionSerializer(exemption_ma).data in response.data['results'],
            'An exemption for the jurisdiction should be included in the list.')
        ok_(ExemptionSerializer(exemption_wa).data not in response.data['results'],
            'An exemption not for the jurisdiction should not be included in the list.')


class TestExemptionCreation(TestCase):
    """
    The exemption creation view allows new exemptions to be submitted for staff review.
    When an exemption is submitted, we need to know the request it was invoked on and the
    language the agency used to invoke it. Then, we should create both an InvokedExemption
    and a NewExemptionTask. Finally, this view should be usable via AJAX (accomodating our
    fancy new exemption browser and submission interface!).
    """
    def setUp(self):
        self.user = UserFactory()
        self.endpoint = '/exemption/'
        self.factory = APIRequestFactory()
        self.view = ExemptionViewSet.as_view({'post': 'create'})

    def test_unauthenticated(self):
        """If the request is unauthenticated, the view should return a 401 status."""
        request = self.factory.post(self.endpoint, {}, format='json')
        response = self.view(request)
        eq_(response.status_code, 401)

    def test_authenticated(self):
        """If the request is authenticated, the view should return a 200 status."""
        request = self.factory.post(self.endpoint, {}, format='json')
        force_authenticate(request, user=self.user)
        response = self.view(request)
        eq_(response.status_code, 200)

