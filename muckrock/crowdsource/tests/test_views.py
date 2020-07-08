"""Tests for crowdsource views"""

# pylint: disable=invalid-name

# Django
from django.contrib.auth.models import AnonymousUser
from django.core.urlresolvers import reverse
from django.test import RequestFactory, TestCase

# Third Party
from nose.tools import assert_false, assert_true, eq_

# MuckRock
from muckrock.core.factories import ProjectFactory, UserFactory
from muckrock.core.test_utils import mock_middleware
from muckrock.crowdsource.factories import (
    CrowdsourceFactory,
    CrowdsourceResponseFactory,
)
from muckrock.crowdsource.views import CrowdsourceDetailView, CrowdsourceFormView


class TestCrowdsourceDetailView(TestCase):
    """Test who is allowed to see the crowdsource details"""

    def setUp(self):
        self.request_factory = RequestFactory()
        self.view = CrowdsourceDetailView.as_view()

    def test_anonymous_cannot_view(self):
        """Anonymous users cannot view a crowdsource's details"""
        crowdsource = CrowdsourceFactory()
        url = reverse(
            "crowdsource-detail",
            kwargs={"slug": crowdsource.slug, "idx": crowdsource.pk},
        )
        request = self.request_factory.get(url)
        request = mock_middleware(request)
        request.user = AnonymousUser()
        response = self.view(request, slug=crowdsource.slug, idx=crowdsource.pk)
        eq_(response.status_code, 302)

    def test_authenticated_cannot_view(self):
        """Authenticated users cannot view a crowdsource's details"""
        crowdsource = CrowdsourceFactory()
        url = reverse(
            "crowdsource-detail",
            kwargs={"slug": crowdsource.slug, "idx": crowdsource.pk},
        )
        request = self.request_factory.get(url)
        request = mock_middleware(request)
        request.user = UserFactory()
        response = self.view(request, slug=crowdsource.slug, idx=crowdsource.pk)
        eq_(response.status_code, 302)

    def test_owner_can_view(self):
        """Owner can view a crowdsource's details"""
        crowdsource = CrowdsourceFactory()
        url = reverse(
            "crowdsource-detail",
            kwargs={"slug": crowdsource.slug, "idx": crowdsource.pk},
        )
        request = self.request_factory.get(url)
        request = mock_middleware(request)
        request.user = crowdsource.user
        response = self.view(request, slug=crowdsource.slug, idx=crowdsource.pk)
        eq_(response.status_code, 200)

    def test_staff_can_view(self):
        """Staff can view a crowdsource's details"""
        crowdsource = CrowdsourceFactory()
        url = reverse(
            "crowdsource-detail",
            kwargs={"slug": crowdsource.slug, "idx": crowdsource.pk},
        )
        request = self.request_factory.get(url)
        request = mock_middleware(request)
        request.user = UserFactory(is_staff=True)
        response = self.view(request, slug=crowdsource.slug, idx=crowdsource.pk)
        eq_(response.status_code, 200)

    def test_project_admin_can_view(self):
        """Project admin can view a crowdsource's details"""
        project = ProjectFactory()
        crowdsource = CrowdsourceFactory(project_admin=True, project=project)
        url = reverse(
            "crowdsource-detail",
            kwargs={"slug": crowdsource.slug, "idx": crowdsource.pk},
        )
        request = self.request_factory.get(url)
        request = mock_middleware(request)
        request.user = UserFactory()
        project.contributors.add(request.user)
        response = self.view(request, slug=crowdsource.slug, idx=crowdsource.pk)
        eq_(response.status_code, 200)

    def test_project_non_admin_cannot_view(self):
        """Project contributor cannot view a crowdsource's details if project
        admin option is not on
        """
        project = ProjectFactory()
        crowdsource = CrowdsourceFactory(project_admin=False, project=project)
        url = reverse(
            "crowdsource-detail",
            kwargs={"slug": crowdsource.slug, "idx": crowdsource.pk},
        )
        request = self.request_factory.get(url)
        request = mock_middleware(request)
        request.user = UserFactory()
        project.contributors.add(request.user)
        response = self.view(request, slug=crowdsource.slug, idx=crowdsource.pk)
        eq_(response.status_code, 302)


class TestCrowdsourceFormView(TestCase):
    """Test who is allowed to fill out assignment forms"""

    def setUp(self):
        self.request_factory = RequestFactory()
        self.view = CrowdsourceFormView.as_view()

    def test_public(self):
        """Anybody can fill out a public assignment"""
        crowdsource = CrowdsourceFactory(status="open")
        url = reverse(
            "crowdsource-assignment",
            kwargs={"slug": crowdsource.slug, "idx": crowdsource.pk},
        )
        request = self.request_factory.get(url)
        request = mock_middleware(request)
        request.user = AnonymousUser()
        response = self.view(request, slug=crowdsource.slug, idx=crowdsource.pk)
        eq_(response.status_code, 200)

    def test_private(self):
        """Everybody cannot fill out a private assignment"""
        project = ProjectFactory()
        crowdsource = CrowdsourceFactory(
            status="open", project_only=True, project=project
        )
        url = reverse(
            "crowdsource-assignment",
            kwargs={"slug": crowdsource.slug, "idx": crowdsource.pk},
        )
        request = self.request_factory.get(url)
        request = mock_middleware(request)
        request.user = AnonymousUser()
        response = self.view(request, slug=crowdsource.slug, idx=crowdsource.pk)
        eq_(response.status_code, 302)

    def test_project(self):
        """Project members can fill out a private assignment"""
        project = ProjectFactory()
        crowdsource = CrowdsourceFactory(
            status="open", project_only=True, project=project
        )
        url = reverse(
            "crowdsource-assignment",
            kwargs={"slug": crowdsource.slug, "idx": crowdsource.pk},
        )
        request = self.request_factory.get(url)
        request = mock_middleware(request)
        request.user = UserFactory()
        project.contributors.add(request.user)
        response = self.view(request, slug=crowdsource.slug, idx=crowdsource.pk)
        eq_(response.status_code, 200)

    def test_owner(self):
        """Crowdsource owner can fill out a private assignment"""
        project = ProjectFactory()
        crowdsource = CrowdsourceFactory(
            status="open", project_only=True, project=project
        )
        url = reverse(
            "crowdsource-assignment",
            kwargs={"slug": crowdsource.slug, "idx": crowdsource.pk},
        )
        request = self.request_factory.get(url)
        request = mock_middleware(request)
        request.user = crowdsource.user
        response = self.view(request, slug=crowdsource.slug, idx=crowdsource.pk)
        eq_(response.status_code, 200)

    def test_has_assignment_limit(self):
        """Test the has assignment method with a user limit"""
        # pylint: disable=protected-access
        view = CrowdsourceFormView()
        crowdsource = CrowdsourceFactory(user_limit=True)
        user = UserFactory()
        ip_address = "127.0.0.1"

        # the user hasn't replied yet, should have an assignment
        assert_true(view._has_assignment(crowdsource, user, None))

        # the user replied, they may not reply again
        CrowdsourceResponseFactory(crowdsource=crowdsource, user=user)
        assert_false(view._has_assignment(crowdsource, user, None))

        # the ip address hasn't replied yet, should have an assignment
        assert_true(view._has_assignment(crowdsource, AnonymousUser(), ip_address))

        # the ip address replied, they may not reply again
        CrowdsourceResponseFactory(
            crowdsource=crowdsource, user=None, ip_address=ip_address
        )
        assert_false(view._has_assignment(crowdsource, AnonymousUser(), ip_address))

    def test_has_assignment_no_limit(self):
        """Test the has assignment method without a user limit"""
        # pylint: disable=protected-access
        view = CrowdsourceFormView()
        crowdsource = CrowdsourceFactory(user_limit=False)
        user = UserFactory()
        ip_address = "127.0.0.1"

        # should always return true

        # the user hasn't replied yet, should have an assignment
        assert_true(view._has_assignment(crowdsource, user, None))

        # the user replied, they may reply again
        CrowdsourceResponseFactory(crowdsource=crowdsource, user=user)
        assert_true(view._has_assignment(crowdsource, user, None))

        # the ip address hasn't replied yet, should have an assignment
        assert_true(view._has_assignment(crowdsource, AnonymousUser(), ip_address))

        # the ip address replied, they may reply again
        CrowdsourceResponseFactory(
            crowdsource=crowdsource, user=None, ip_address=ip_address
        )
        assert_true(view._has_assignment(crowdsource, AnonymousUser(), ip_address))
