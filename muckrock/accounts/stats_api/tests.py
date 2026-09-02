# Django
from django.utils import timezone

# Standard Library
import json
from datetime import timedelta
from unittest.mock import patch

# Third Party
import pytest
from rest_framework import status

# MuckRock
from muckrock.accounts.stats_api.models import UserStats
from muckrock.core.factories import AgencyFactory, UserFactory
from muckrock.core.utils import record_request_filed
from muckrock.foia.factories import FOIAComposerFactory, FOIARequestFactory
from muckrock.organization.factories import MembershipFactory, OrganizationFactory
from muckrock.organization.stats_api.models import OrganizationStats


@pytest.mark.django_db()
class TestUserStatsAPI:
    def _admin(self):
        return UserFactory(is_staff=True)

    def _filed(self, user, submitted_at, foias=1):
        composer = FOIAComposerFactory(
            user=user,
            organization=user.profile.organization,
            status="filed",
            datetime_submitted=submitted_at,
        )
        FOIARequestFactory.create_batch(foias, composer=composer)
        return composer

    def test_list(self, api_client):
        api_client.force_authenticate(user=self._admin())
        UserFactory.create_batch(3)
        response = api_client.get("/stats_api/users/")
        assert response.status_code == status.HTTP_200_OK
        body = json.loads(response.content)
        # admin + 3 created (plus possibly others); assert at least the ones we made
        assert len(body["results"]) >= 4

    def test_list_requires_admin(self, api_client):
        api_client.force_authenticate(user=UserFactory())  # non-staff
        response = api_client.get("/stats_api/users/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_unauthenticated(self, api_client):
        response = api_client.get("/stats_api/users/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_populates_enriched_fields(self, api_client):
        """Regression: detail view must populate individual_requests and the
        annotated counts, not just the list view (they were only set in
        paginate_queryset before)."""
        api_client.force_authenticate(user=self._admin())

        target = UserFactory()
        org = target.profile.organization
        org.monthly_requests = 5
        org.requests_per_month = 10
        org.number_requests = 3
        org.save()
        self._filed(target, timezone.now(), foias=2)

        response = api_client.get(f"/stats_api/users/{target.profile.uuid}/")
        assert response.status_code == status.HTTP_200_OK
        body = json.loads(response.content)

        assert body["total_requests"] == 2
        assert body["recent_request_count"] == 2
        # individual-org balance dict — raw fields off the personal org
        assert body["individual_requests"]["monthly_requests"] == 5
        assert body["individual_requests"]["requests_per_month"] == 10
        assert body["individual_requests"]["number_requests"] == 3

    def test_filter_filed_within_days(self, api_client):
        api_client.force_authenticate(user=self._admin())
        now = timezone.now()

        recent = UserFactory()
        UserStats.objects.filter(user=recent).update(
            last_request_at=now - timedelta(days=1)
        )
        old = UserFactory()
        UserStats.objects.filter(user=old).update(
            last_request_at=now - timedelta(days=30)
        )

        response = api_client.get("/stats_api/users/", {"filed_within_days": 7})
        assert response.status_code == status.HTTP_200_OK
        uuids = {r["uuid"] for r in json.loads(response.content)["results"]}
        assert str(recent.profile.uuid) in uuids
        assert str(old.profile.uuid) not in uuids

    def test_filter_logged_in_within_days(self, api_client):
        api_client.force_authenticate(user=self._admin())
        now = timezone.now()

        recent = UserFactory(last_login=now - timedelta(days=1))
        old = UserFactory(last_login=now - timedelta(days=30))

        response = api_client.get("/stats_api/users/", {"logged_in_within_days": 7})
        uuids = {r["uuid"] for r in json.loads(response.content)["results"]}
        assert str(recent.profile.uuid) in uuids
        assert str(old.profile.uuid) not in uuids

    def test_active_within_days_is_filed_or_login(self, api_client):
        """active = filed a request OR logged in."""
        api_client.force_authenticate(user=self._admin())
        now = timezone.now()

        filer = UserFactory(last_login=now - timedelta(days=90))
        UserStats.objects.filter(user=filer).update(
            last_request_at=now - timedelta(days=1)
        )
        logged_in = UserFactory(last_login=now - timedelta(days=1))
        inactive = UserFactory(last_login=now - timedelta(days=90))
        UserStats.objects.filter(user=inactive).update(
            last_request_at=now - timedelta(days=90)
        )

        response = api_client.get("/stats_api/users/", {"active_within_days": 7})
        uuids = {r["uuid"] for r in json.loads(response.content)["results"]}
        assert str(filer.profile.uuid) in uuids
        assert str(logged_in.profile.uuid) in uuids
        assert str(inactive.profile.uuid) not in uuids

    def test_record_request_filed_sets_watermarks(self):
        """record_request_filed bumps the user watermark and the org watermark
        for collective orgs."""

        user = UserFactory()
        org = OrganizationFactory(individual=False)
        MembershipFactory(user=user, organization=org)

        # UserStats created by the user signal; OrganizationStats by the
        # collective-org signal.
        when = timezone.now()
        record_request_filed(user_id=user.pk, organization_id=org.pk, when=when)

        assert UserStats.objects.get(user=user).last_request_at == when
        assert OrganizationStats.objects.get(organization=org).last_request_at == when

    def test_record_request_filed_skips_individual_org(self):
        """Individual orgs have no stats row; recording is a silent no-op, not a
        crash (record_request_filed uses .filter().update())."""

        user = UserFactory()
        individual_org = user.profile.organization
        assert not OrganizationStats.objects.filter(
            organization=individual_org
        ).exists()

        record_request_filed(
            user_id=user.pk, organization_id=individual_org.pk, when=timezone.now()
        )

        # user watermark still set; org simply has no row to update
        assert UserStats.objects.get(user=user).last_request_at is not None
        assert not OrganizationStats.objects.filter(
            organization=individual_org
        ).exists()

    def test_submit_bumps_watermarks(self):
        """The real composer.submit() path records the filing watermark on both
        the user and a collective org."""

        user = UserFactory()
        org = OrganizationFactory(individual=False)
        MembershipFactory(user=user, organization=org)
        org.monthly_requests = 5
        org.save()

        agency = AgencyFactory()
        composer = FOIAComposerFactory(user=user, organization=org, agencies=[agency])

        with patch("muckrock.foia.tasks.composer_create_foias"), patch(
            "muckrock.foia.tasks.composer_delayed_submit"
        ) as delayed, patch("muckrock.foia.models.composer.mailchimp_journey"):
            delayed.apply_async.return_value.id = "test-id"
            composer.submit()

        assert UserStats.objects.get(user=user).last_request_at is not None
        assert (
            OrganizationStats.objects.get(organization=org).last_request_at is not None
        )
