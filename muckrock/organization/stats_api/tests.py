# Django
from django.conf import settings
from django.test import TestCase
from django.utils import timezone

# Standard Library
import json
from datetime import timedelta

# Third Party
import pytest
from rest_framework import status

# MuckRock
from muckrock.core.factories import UserFactory
from muckrock.foia.factories import FOIAComposerFactory, FOIARequestFactory
from muckrock.organization.factories import OrganizationFactory
from muckrock.organization.models import Organization
from muckrock.organization.stats_api.models import OrganizationStats


class OrgTotalRequestsQueryTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.parent = OrganizationFactory(
            share_resources=True,
            number_requests=100,
            monthly_requests=100,
            requests_per_month=100,
        )
        cls.org = OrganizationFactory(
            parent=cls.parent,
            share_resources=True,
            number_requests=10,
            monthly_requests=10,
            requests_per_month=10,
        )
        cls.sharing_group = OrganizationFactory(
            share_resources=True,
            number_requests=5,
            monthly_requests=5,
            requests_per_month=5,
        )
        cls.non_sharing_group = OrganizationFactory(
            share_resources=False,
            number_requests=999,
            monthly_requests=999,
            requests_per_month=999,
        )
        cls.org.groups.set([cls.sharing_group, cls.non_sharing_group])

    def test_total_requests_use_prefetch_cache(self):
        # Mirror the stats endpoint's fetch.
        org = (
            Organization.objects.select_related("parent")
            .prefetch_related("groups")
            .get(pk=self.org.pk)
        )
        # Regression against N+1 in the get_total_* methods:
        # parent (select_related) + groups (prefetch) already loaded.
        with self.assertNumQueries(0):
            org.get_total_number_requests()
            org.get_total_monthly_requests()
            org.get_total_requests_per_month()

    def test_totals_are_correct(self):
        org = (
            Organization.objects.select_related("parent")
            .prefetch_related("groups")
            .get(pk=self.org.pk)
        )
        # self + sharing parent + sharing group; non_sharing_group's 999 excluded.
        self.assertEqual(org.get_total_number_requests(), 10 + 100 + 5)
        self.assertEqual(org.get_total_monthly_requests(), 10 + 100 + 5)
        self.assertEqual(org.get_total_requests_per_month(), 10 + 100 + 5)

    def test_totals_match_make_requests_consumption(self):
        org = Organization.objects.get(pk=self.org.pk)
        total_monthly = org.get_total_monthly_requests()
        total_number = org.get_total_number_requests()
        consumed = org.make_requests(total_monthly + total_number)
        self.assertEqual(consumed["monthly"], total_monthly)
        self.assertEqual(consumed["regular"], total_number)


@pytest.mark.django_db()
class TestOrganizationStatsAPI:
    def _admin(self):
        return UserFactory(is_staff=True)

    def _submitted_composer(self, org, submitted_at, foias=1):
        composer = FOIAComposerFactory(
            organization=org,
            status="filed",
            datetime_submitted=submitted_at,
        )
        FOIARequestFactory.create_batch(foias, composer=composer)
        return composer

    def test_list_requires_admin(self, api_client):
        api_client.force_authenticate(user=UserFactory())
        response = api_client.get("/stats_api/organizations/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_unauthenticated(self, api_client):
        response = api_client.get("/stats_api/organizations/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_excludes_individual_orgs(self, api_client):
        """Individual orgs are pulled in on the users endpoint, not here."""
        api_client.force_authenticate(user=self._admin())
        collective = OrganizationFactory.create_batch(3, individual=False)
        individual = OrganizationFactory(individual=True)
        response = api_client.get("/stats_api/organizations/")
        assert response.status_code == status.HTTP_200_OK
        uuids = {r["uuid"] for r in json.loads(response.content)["results"]}
        for org in collective:
            assert str(org.uuid) in uuids
        # get_queryset excludes individual=True
        assert str(individual.uuid) not in uuids

    def test_retrieve_populates_enriched_fields(self, api_client):
        """Regression: detail view must populate the annotated counts, which were
        previously only set in paginate_queryset (list view)."""
        api_client.force_authenticate(user=self._admin())
        org = OrganizationFactory(individual=False)
        self._submitted_composer(org, timezone.now(), foias=2)

        response = api_client.get(f"/stats_api/organizations/{org.uuid}/")
        assert response.status_code == status.HTTP_200_OK
        body = json.loads(response.content)
        assert body["total_requests"] == 2
        assert body["recent_request_count"] == 2

    def test_filter_filed_within_days(self, api_client):
        api_client.force_authenticate(user=self._admin())
        now = timezone.now()

        recent = OrganizationFactory(individual=False)
        OrganizationStats.objects.filter(organization=recent).update(
            last_request_at=now - timedelta(days=1)
        )
        old = OrganizationFactory(individual=False)
        OrganizationStats.objects.filter(organization=old).update(
            last_request_at=now - timedelta(days=30)
        )

        response = api_client.get("/stats_api/organizations/", {"filed_within_days": 7})
        assert response.status_code == status.HTTP_200_OK
        uuids = {r["uuid"] for r in json.loads(response.content)["results"]}
        assert str(recent.uuid) in uuids
        assert str(old.uuid) not in uuids

    def test_aged_out_requires_since(self, api_client):
        api_client.force_authenticate(user=self._admin())
        response = api_client.get("/stats_api/organizations/aged_out/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_aged_out_invalid_since(self, api_client):
        api_client.force_authenticate(user=self._admin())
        response = api_client.get(
            "/stats_api/organizations/aged_out/", {"since": "not-a-date"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_aged_out_returns_boundary_crossers(self, api_client):
        api_client.force_authenticate(user=self._admin())
        now = timezone.now()
        win = timedelta(days=settings.REQUEST_WINDOW_DAYS)

        # org with a request that aged out of the window since `since`
        aged = OrganizationFactory(individual=False)
        self._submitted_composer(aged, now - win - timedelta(days=1))

        # org with only a fresh filing — still in window, should NOT appear
        fresh = OrganizationFactory(individual=False)
        self._submitted_composer(fresh, now)

        since = (now - timedelta(days=2)).isoformat()
        response = api_client.get(
            "/stats_api/organizations/aged_out/", {"since": since}
        )
        assert response.status_code == status.HTTP_200_OK
        uuids = {r["uuid"] for r in json.loads(response.content)["results"]}
        assert str(aged.uuid) in uuids
        assert str(fresh.uuid) not in uuids
