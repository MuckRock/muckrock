# Django
from django.contrib.auth.models import Permission, User
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
from muckrock.foia.models import FOIARequest
from muckrock.organization.factories import MembershipFactory, OrganizationFactory


def _grant(user, codename):
    """Grant a permission and return the user with a fresh permission cache"""
    user.user_permissions.add(Permission.objects.get(codename=codename))
    return User.objects.get(pk=user.pk)


def _fund(org, amount=5):
    """Give an org a request balance so submit() succeeds"""
    org.number_requests = amount
    org.save()
    return org


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
        _fund(user.profile.organization)
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

    def test_create_missing_agencies(self):
        """Omitting agencies returns 400 (previously a 500 KeyError)"""
        user = UserFactory.create()
        self.client.force_authenticate(user=user)
        response = self.client.post(
            reverse("api2-requests-list"),
            {"title": "Test", "requested_docs": "Meeting minutes"},
        )
        assert response.status_code == 400, response.json()
        assert "agencies" in response.json()

    def test_create_empty_agencies(self):
        """Empty agencies list returns 400"""
        user = UserFactory.create()
        self.client.force_authenticate(user=user)
        response = self.client.post(
            reverse("api2-requests-list"),
            {"agencies": [], "title": "Test", "requested_docs": "Meeting minutes"},
        )
        assert response.status_code == 400, response.json()

    def test_create_unapproved_agency(self):
        """A non-approved agency is not in the serializer queryset, yielding 400"""
        agency = AgencyFactory.create(status="pending")
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
        assert response.status_code == 400, response.json()

    def test_create_missing_title(self):
        """Omitting title returns 400"""
        agency = AgencyFactory.create()
        user = UserFactory.create()
        self.client.force_authenticate(user=user)
        response = self.client.post(
            reverse("api2-requests-list"),
            {"agencies": [agency.pk], "requested_docs": "Meeting minutes"},
        )
        assert response.status_code == 400, response.json()

    def test_create_missing_requested_docs(self):
        """Omitting requested_docs returns 400"""
        agency = AgencyFactory.create()
        user = UserFactory.create()
        self.client.force_authenticate(user=user)
        response = self.client.post(
            reverse("api2-requests-list"),
            {"agencies": [agency.pk], "title": "Test"},
        )
        assert response.status_code == 400, response.json()

    def test_create_insufficient_requests(self):
        """Valid payload but no request balance returns 402, not 500"""
        agency = AgencyFactory.create()
        user = UserFactory.create()  # individual org, zero balance
        self.client.force_authenticate(user=user)
        response = self.client.post(
            reverse("api2-requests-list"),
            {
                "agencies": [agency.pk],
                "title": "Test",
                "requested_docs": "Meeting minutes",
            },
        )
        assert response.status_code == 402, response.json()

    def test_create_defaults_to_personal_org(self):
        """Omitting organization files under the user's individual org"""
        agency = AgencyFactory.create()
        user = UserFactory.create()
        personal_org = user.profile.organization
        _fund(personal_org)
        self.client.force_authenticate(user=user)
        response = self.client.post(
            reverse("api2-requests-list"),
            {
                "agencies": [agency.pk],
                "title": "Test",
                "requested_docs": "Meeting minutes",
            },
            format="json",
        )
        assert response.status_code == 201, response.json()
        foia = FOIARequest.objects.get(pk=response.json()["requests"][0])
        assert foia.composer.organization == personal_org

    def test_create_bills_the_named_organization(self):
        """The composer is billed to the org the user selected, not their default"""
        agency = AgencyFactory.create()
        user = UserFactory.create()
        org = OrganizationFactory.create()
        MembershipFactory.create(user=user, organization=org)
        _fund(org)
        self.client.force_authenticate(user=user)
        response = self.client.post(
            reverse("api2-requests-list"),
            {
                "agencies": [agency.pk],
                "title": "Test",
                "requested_docs": "Meeting minutes",
                "organization": org.pk,
            },
            format="json",
        )
        assert response.status_code == 201, response.json()
        foia = FOIARequest.objects.get(pk=response.json()["requests"][0])
        assert foia.composer.organization == org
        # the named org was debited, not the user's personal org
        org.refresh_from_db()
        assert org.number_requests == 4

    def test_create_nonexistent_organization_rejected(self):
        """A nonexistent org PK fails validation (400)"""
        agency = AgencyFactory.create()
        user = UserFactory.create()
        self.client.force_authenticate(user=user)
        response = self.client.post(
            reverse("api2-requests-list"),
            {
                "agencies": [agency.pk],
                "title": "Test",
                "requested_docs": "Meeting minutes",
                "organization": 99999999,
            },
            format="json",
        )
        assert response.status_code == 400, response.json()
        assert "organization" in response.json()

    def test_create_personal_org_explicitly(self):
        """A user can explicitly name their own individual org"""
        agency = AgencyFactory.create()
        user = UserFactory.create()
        personal_org = user.profile.organization
        _fund(personal_org)
        self.client.force_authenticate(user=user)
        response = self.client.post(
            reverse("api2-requests-list"),
            {
                "agencies": [agency.pk],
                "title": "Test",
                "requested_docs": "Meeting minutes",
                "organization": personal_org.pk,
            },
            format="json",
        )
        assert response.status_code == 201, response.json()
        foia = FOIARequest.objects.get(pk=response.json()["requests"][0])
        assert foia.composer.organization == personal_org

    def test_create_edited_boilerplate(self):
        """edited_boilerplate is settable on create and persists to the composer"""
        agency = AgencyFactory.create()
        user = UserFactory.create()
        _fund(user.profile.organization)
        self.client.force_authenticate(user=user)
        response = self.client.post(
            reverse("api2-requests-list"),
            {
                "agencies": [agency.pk],
                "title": "Test",
                "requested_docs": "Meeting minutes",
                "edited_boilerplate": True,
            },
        )
        assert response.status_code == 201, response.json()
        foia = FOIARequest.objects.get(pk=response.json()["requests"][0])
        assert foia.composer.edited_boilerplate is True

    def test_create_edited_boilerplate_defaults_false(self):
        """Omitting edited_boilerplate defaults to False"""
        agency = AgencyFactory.create()
        user = UserFactory.create()
        _fund(user.profile.organization)
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
        foia = FOIARequest.objects.get(pk=response.json()["requests"][0])
        assert foia.composer.edited_boilerplate is False

    def test_create_embargo_without_permission_rejected(self):
        """Setting embargo without permission returns 400 with a message"""
        agency = AgencyFactory.create()
        user = UserFactory.create()
        _fund(user.profile.organization)
        self.client.force_authenticate(user=user)
        response = self.client.post(
            reverse("api2-requests-list"),
            {
                "agencies": [agency.pk],
                "title": "Test",
                "requested_docs": "Meeting minutes",
                "embargo_status": "embargo",
            },
        )
        assert response.status_code == 400, response.json()
        assert "embargo_status" in response.json()

    def test_create_embargo_with_permission(self):
        """With embargo permission, embargo_status is honored"""
        agency = AgencyFactory.create()
        user = _grant(UserFactory.create(), "embargo_foiarequest")
        _fund(user.profile.organization)
        self.client.force_authenticate(user=user)
        response = self.client.post(
            reverse("api2-requests-list"),
            {
                "agencies": [agency.pk],
                "title": "Test",
                "requested_docs": "Meeting minutes",
                "embargo_status": "embargo",
            },
        )
        assert response.status_code == 201, response.json()
        foia = FOIARequest.objects.get(pk=response.json()["requests"][0])
        assert foia.composer.embargo_status == "embargo"

    def test_create_public_needs_no_permission(self):
        """Explicitly setting public requires no embargo permission"""
        agency = AgencyFactory.create()
        user = UserFactory.create()
        _fund(user.profile.organization)
        self.client.force_authenticate(user=user)
        response = self.client.post(
            reverse("api2-requests-list"),
            {
                "agencies": [agency.pk],
                "title": "Test",
                "requested_docs": "Meeting minutes",
                "embargo_status": "public",
            },
        )
        assert response.status_code == 201, response.json()

    def test_create_permanent_embargo_without_permission(self):
        """embargo perm but not perm-embargo perm: 'permanent' is rejected (400)"""
        agency = AgencyFactory.create()
        user = _grant(UserFactory.create(), "embargo_foiarequest")
        _fund(user.profile.organization)
        self.client.force_authenticate(user=user)
        response = self.client.post(
            reverse("api2-requests-list"),
            {
                "agencies": [agency.pk],
                "title": "Test",
                "requested_docs": "Meeting minutes",
                "embargo_status": "permanent",
            },
        )
        assert response.status_code == 400, response.json()

    def test_create_invalid_embargo_status(self):
        """A permitted user sending an invalid choice gets a 400"""
        agency = AgencyFactory.create()
        user = _grant(UserFactory.create(), "embargo_foiarequest")
        _fund(user.profile.organization)
        self.client.force_authenticate(user=user)
        response = self.client.post(
            reverse("api2-requests-list"),
            {
                "agencies": [agency.pk],
                "title": "Test",
                "requested_docs": "Meeting minutes",
                "embargo_status": "not_a_real_value",
            },
        )
        assert response.status_code == 400, response.json()

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
