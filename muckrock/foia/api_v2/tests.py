# Django
from django.test import TestCase
from django.urls import reverse

# Third Party
from nose.tools import eq_

# MuckRock
from muckrock.foia.factories import FOIACommunicationFactory, FOIARequestFactory


class TestFOIARequestViewset(TestCase):

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
