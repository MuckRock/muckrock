"""
Test the FOIA API
"""

# Django
from django.test import TestCase

# Third Party
from nose.tools import eq_, ok_
from rest_framework.test import APIRequestFactory, force_authenticate

# MuckRock
from muckrock.core.factories import AgencyFactory, UserFactory
from muckrock.foia.models.request import FOIARequest
from muckrock.foia.viewsets import FOIARequestViewSet
from muckrock.organization.factories import MembershipFactory, OrganizationFactory


class TestFoiaCreation(TestCase):
    """
    Test creating a FOIA via the API
    """

    def setUp(self):
        self.endpoint = "/foia/"
        self.factory = APIRequestFactory()
        self.view = FOIARequestViewSet.as_view({"post": "create"})
        self.user = UserFactory()
        self.agency = AgencyFactory()
        self.organization = OrganizationFactory(number_requests=10)
        MembershipFactory(user=self.user, organization=self.organization, active=False)

    def test_create(self):
        """Create a FOIA Request"""

        data = {
            "agency": [self.agency.pk],
            "title": "Test request",
            "document_request": "Best cake recipe",
        }
        self.user.profile.organization.number_requests = 10
        self.user.profile.organization.save()
        request = self.factory.post(self.endpoint, data, format="json")
        force_authenticate(request, user=self.user)
        response = self.view(request)
        eq_(response.status_code, 201)

        request_ids = response.data["Requests"]
        foia = FOIARequest.objects.get(pk=request_ids[0])
        assert foia.composer.organization == self.user.profile.organization

    def test_create_org(self):
        """Create a FOIA Request with a specified org"""

        data = {
            "agency": [self.agency.pk],
            "title": "Test request",
            "document_request": "Best cake recipe",
            "organization": self.organization.slug,
        }
        request = self.factory.post(self.endpoint, data, format="json")
        force_authenticate(request, user=self.user)
        response = self.view(request)
        eq_(response.status_code, 201)

        request_ids = response.data["Requests"]
        foia = FOIARequest.objects.get(pk=request_ids[0])
        assert foia.composer.organization == self.organization

    def test_create_org_bad(self):
        """Create a FOIA Request with a specified org"""

        org = OrganizationFactory()
        assert not org.has_member(self.user)
        data = {
            "agency": [self.agency.pk],
            "title": "Test request",
            "document_request": "Best cake recipe",
            "organization": org.slug,
        }
        self.user.profile.organization.number_requests = 10
        self.user.profile.organization.save()
        request = self.factory.post(self.endpoint, data, format="json")
        force_authenticate(request, user=self.user)
        response = self.view(request)
        eq_(response.status_code, 400)
