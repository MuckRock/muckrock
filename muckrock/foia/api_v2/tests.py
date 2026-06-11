# Django
from django.test import TestCase
from django.urls import reverse

# Third Party
from rest_framework.test import APIClient

# MuckRock
from muckrock.core.factories import AgencyFactory, UserFactory
from muckrock.foia.factories import (
    FOIACommunicationFactory,
    FOIAFileFactory,
    FOIARequestFactory,
)


class TestFOIARequestViewset(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory.create()

    def test_detail(self):
        self.client.force_authenticate(user=self.user)
        foia = FOIARequestFactory.create()
        response = self.client.get(
            reverse("api2-requests-detail", kwargs={"pk": foia.pk}),
        )
        assert response.status_code == 200

    def test_list(self):
        self.client.force_authenticate(user=self.user)
        FOIARequestFactory.create()
        response = self.client.get(reverse("api2-requests-list"))
        assert response.status_code == 200

    def test_create(self):
        agency = AgencyFactory.create()
        user = UserFactory.create()
        self.client.force_authenticate(user=user)
        response = self.client.post(
            reverse("api2-requests-list"),
            {
                "agencies": [agency.pk],
                "title": "Test",
                "requested_docs": "Meeting minutes",
            },
        )
        assert response.status_code == 201, response.json()

    def test_unauthenticated_cannot_list(self):
        response = self.client.get(reverse("api2-requests-list"))
        assert response.status_code == 401

    def test_unauthenticated_cannot_retrieve(self):
        foia = FOIARequestFactory.create()
        response = self.client.get(
            reverse("api2-requests-detail", kwargs={"pk": foia.pk})
        )
        assert response.status_code == 401


class TestFOIACommunicationViewset(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory.create()

    def test_detail(self):
        self.client.force_authenticate(user=self.user)
        comm = FOIACommunicationFactory.create()
        response = self.client.get(
            reverse("api2-communications-detail", kwargs={"pk": comm.pk}),
        )
        assert response.status_code == 200

    def test_list(self):
        self.client.force_authenticate(user=self.user)
        FOIACommunicationFactory.create()
        response = self.client.get(reverse("api2-communications-list"))
        assert response.status_code == 200

    def test_unauthenticated_cannot_list(self):
        response = self.client.get(reverse("api2-communications-list"))
        assert response.status_code == 401

    def test_unauthenticated_cannot_retrieve(self):
        comm = FOIACommunicationFactory.create()
        response = self.client.get(
            reverse("api2-communications-detail", kwargs={"pk": comm.pk})
        )
        assert response.status_code == 401


class TestFOIAFileViewset(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory.create()

    def test_detail(self):
        self.client.force_authenticate(user=self.user)
        file = FOIAFileFactory.create()
        response = self.client.get(reverse("api2-files-detail", kwargs={"pk": file.pk}))
        assert response.status_code == 200

    def test_list(self):
        self.client.force_authenticate(user=self.user)
        FOIAFileFactory.create()
        response = self.client.get(reverse("api2-files-list"))
        assert response.status_code == 200

    def test_unauthenticated_cannot_list(self):
        response = self.client.get(reverse("api2-files-list"))
        assert response.status_code == 401

    def test_unauthenticated_cannot_retrieve(self):
        file = FOIAFileFactory.create()
        response = self.client.get(reverse("api2-files-detail", kwargs={"pk": file.pk}))
        assert response.status_code == 401
