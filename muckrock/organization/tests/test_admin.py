"""
Tests for the organization admin
"""

# Django
from django.conf import settings
from django.test import TestCase
from django.urls import reverse

# Standard Library
import json

# Third Party
from reversion.models import Version

# MuckRock
from muckrock.core.factories import UserFactory
from muckrock.organization.factories import OrganizationFactory
from muckrock.organization.models import Organization


class TestOrganizationAdminRequestChange(TestCase):
    """Purchased requests can only be adjusted by a delta in the admin"""

    def setUp(self):
        self.superuser = UserFactory(is_staff=True, is_superuser=True)
        self.client.force_login(self.superuser)
        self.org = OrganizationFactory(number_requests=5)
        self.url = reverse(
            "admin:organization_organization_change", args=(self.org.pk,)
        )

    def post_change(self, data):
        """Submit the org change form"""
        data["_save"] = "Save"
        return self.client.post(self.url, data)

    def get_balance(self):
        """Current purchased request balance from the database"""
        return Organization.objects.get(pk=self.org.pk).number_requests

    def test_add_requests(self):
        response = self.post_change({"number_requests_change": 3})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.get_balance(), 8)

    def test_remove_requests(self):
        response = self.post_change({"number_requests_change": -2})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.get_balance(), 3)

    def test_change_applies_to_fresh_balance(self):
        self.client.get(self.url)
        # balance changes after the page loaded, e.g. the user files a request
        Organization.objects.filter(pk=self.org.pk).update(number_requests=4)
        self.post_change({"number_requests_change": 3})
        self.assertEqual(self.get_balance(), 7)

    def test_balance_field_is_read_only(self):
        self.post_change({"number_requests": 999, "number_requests_change": 0})
        self.assertEqual(self.get_balance(), 5)

    def test_cannot_go_below_zero(self):
        response = self.post_change({"number_requests_change": -6})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Purchased requests cannot go below 0")
        self.assertEqual(self.get_balance(), 5)

    def test_cannot_exceed_max_change(self):
        response = self.post_change(
            {"number_requests_change": settings.MAX_REQUESTS_CHANGE + 1}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.get_balance(), 5)

    def test_reversion_records_real_balance(self):
        self.post_change({"number_requests_change": 3})
        version = Version.objects.get_for_object(self.org).first()
        fields = json.loads(version.serialized_data)[0]["fields"]
        self.assertEqual(fields["number_requests"], 8)
