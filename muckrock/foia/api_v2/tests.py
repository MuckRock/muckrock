# Django
from django.test import TestCase
from django.urls import reverse

# Third Party
from nose.tools import eq_
from rest_framework.test import APIClient

# MuckRock
from muckrock.agency.models.agency import Agency
from muckrock.core.factories import AgencyFactory, UserFactory
from muckrock.foia.factories import FOIACommunicationFactory, FOIARequestFactory


class TestFOIARequestViewset(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_detail(self):
        foia = FOIARequestFactory.create()
        response = self.client.get(
            reverse("api2-requests-detail", kwargs={"pk": foia.pk}),
        )
        eq_(response.status_code, 200)

    def test_list(self):
        FOIARequestFactory.create()
        response = self.client.get(reverse("api2-requests-list"))
        eq_(response.status_code, 200)

    def test_create(self):
        agency = AgencyFactory.create()
        user = UserFactory.create()
        self.client.force_authenticate(user)
        response = self.client.post(
            reverse("api2-requests-list"),
            {
                "agencies": [agency.pk],
                "title": "Test",
                "requested_docs": "Meeting minutes",
            },
        )
        eq_(response.status_code, 201, response.json())


class TestFOIACommunicationViewset(TestCase):

    def test_detail(self):
        comm = FOIACommunicationFactory.create()
        response = self.client.get(
            reverse("api2-communications-detail", kwargs={"pk": comm.pk}),
        )
        eq_(response.status_code, 200)

    def test_list(self):
        FOIACommunicationFactory.create()
        response = self.client.get(reverse("api2-communications-list"))
        eq_(response.status_code, 200)
