"""
Test the Organization API viewset
"""

# Django
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

# Standard Library
import json
from uuid import uuid4

# Third Party
from nose.tools import assert_false, eq_, ok_
from rest_framework.authtoken.models import Token
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

# MuckRock
from muckrock.core.factories import UserFactory
from muckrock.organization.choices import Plan
from muckrock.organization.factories import OrganizationFactory
from muckrock.organization.models import Membership, Organization

# pylint: disable=invalid-name


class TestOrganizationViewSet(TestCase):
    """Tests for the organization and membership viewsets"""

    def api_call(self, url, method="post", data=None, code=HTTP_200_OK):
        """Helper for API calls"""
        if data is None:
            data = {}

        user = UserFactory.create(is_staff=True)
        Token.objects.create(user=user)

        headers = {
            'content-type': 'application/json',
            'HTTP_AUTHORIZATION': 'Token %s' % user.auth_token,
        }
        response = getattr(self.client, method)(
            url, json.dumps(data), content_type='application/json', **headers
        )
        eq_(
            response.status_code, code,
            'Code: {}\nResponse: {}'.format(response.status_code, response)
        )

    def test_organization_create(self):
        """Test creating an organization"""
        data = {
            'name': 'Test Org',
            'private': False,
            'plan': Plan.free,
            'individual': False,
            'uuid': unicode(uuid4()),
        }
        self.api_call(
            reverse('api-organization-list'),
            'post',
            data,
            code=HTTP_201_CREATED,
        )
        ok_(Organization.objects.filter(**data).exists())

    def test_organization_update(self):
        """Test updating an organization"""
        data = {
            'name': 'Test Org',
            'private': False,
            'plan': Plan.free,
            'individual': False,
            'uuid': unicode(uuid4()),
        }
        OrganizationFactory.create(uuid=data['uuid'])
        self.api_call(
            reverse('api-organization-detail', kwargs={
                'uuid': data['uuid']
            }),
            'patch',
            data,
        )
        ok_(Organization.objects.filter(**data).exists())

    def test_membership_create(self):
        """Test creaintg a membership"""
        organization = OrganizationFactory.create()
        user = UserFactory.create()
        assert_false(organization.has_member(user))
        self.api_call(
            reverse(
                'api-organization-membership-list',
                kwargs={
                    'organization_uuid': organization.uuid,
                }
            ),
            'post',
            {'user': unicode(user.profile.uuid)},
            code=HTTP_201_CREATED,
        )
        ok_(organization.has_member(user))

    def test_membership_delete(self):
        """Test deleting a membership"""
        organization = OrganizationFactory.create()
        user = UserFactory.create()
        Membership.objects.create(organization=organization, user=user)
        ok_(organization.has_member(user))
        self.api_call(
            reverse(
                'api-organization-membership-detail',
                kwargs={
                    'organization_uuid': organization.uuid,
                    'user__profile__uuid': user.profile.uuid,
                }
            ),
            'delete',
            code=HTTP_204_NO_CONTENT,
        )
        assert_false(organization.has_member(user))

    def test_membership_delete_individual(self):
        """Deleting an individual membership should fail"""
        user = UserFactory.create()
        ok_(user.profile.organization.has_member(user))
        self.api_call(
            reverse(
                'api-organization-membership-detail',
                kwargs={
                    'organization_uuid': user.profile.organization.uuid,
                    'user__profile__uuid': user.profile.uuid,
                }
            ),
            'delete',
            code=HTTP_422_UNPROCESSABLE_ENTITY,
        )
        ok_(user.profile.organization.has_member(user))

    def test_membership_delete_active(self):
        """Deleting an active membership should activate the individual membership"""
        organization = OrganizationFactory.create()
        user = UserFactory.create(membership__active=False)
        individual_organization = user.organizations.first()
        ok_(individual_organization.individual)
        Membership.objects.create(
            organization=organization, user=user, active=True
        )
        eq_(user.profile.organization, organization)
        self.api_call(
            reverse(
                'api-organization-membership-detail',
                kwargs={
                    'organization_uuid': organization.uuid,
                    'user__profile__uuid': user.profile.uuid,
                }
            ),
            'delete',
            code=HTTP_204_NO_CONTENT,
        )
        # user's organization is cached on the object, so refetch object from db
        user = User.objects.get(pk=user.pk)
        eq_(user.profile.organization, individual_organization)
