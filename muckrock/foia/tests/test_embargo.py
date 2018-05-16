"""
Tests embargo features on a request
"""

# Django
from django.test import RequestFactory, TestCase

# Standard Library
import datetime

# Third Party
from nose.tools import assert_false, assert_true, eq_, ok_

# MuckRock
from muckrock.core.factories import OrganizationFactory, UserFactory
from muckrock.core.test_utils import mock_middleware
from muckrock.foia.factories import FOIARequestFactory
from muckrock.foia.forms import FOIAEmbargoForm
from muckrock.foia.models import END_STATUS
from muckrock.foia.tasks import embargo_expire
from muckrock.foia.views import embargo


class TestEmbargo(TestCase):
    """Embargoing a request hides it from public view."""

    def setUp(self):
        self.user = UserFactory(profile__acct_type='pro')
        self.user.profile.organization = OrganizationFactory(active=True)
        self.foia = FOIARequestFactory(composer__user=self.user)
        self.request_factory = RequestFactory()
        self.url = self.foia.get_absolute_url()

    def get_response(self, request):
        """Utility function for calling the embargo view function"""
        request = mock_middleware(request)
        return embargo(
            request,
            self.foia.jurisdiction.slug,
            self.foia.jurisdiction.pk,
            self.foia.slug,
            self.foia.pk,
        )

    def test_basic_embargo(self):
        """The embargo should be accepted if the owner can embargo and edit the request."""
        ok_(
            self.foia.has_perm(self.user, 'change'),
            'The request should be editable by the user.'
        )
        ok_(
            self.foia.has_perm(self.user, 'embargo'),
            'The user should be allowed to embargo.'
        )
        ok_(
            self.foia.status not in END_STATUS,
            'The request should not be closed.'
        )
        data = {'embargo': 'create'}
        request = self.request_factory.post(self.url, data)
        request.user = self.user
        response = self.get_response(request)
        self.foia.refresh_from_db()
        eq_(response.status_code, 302)
        ok_(self.foia.embargo, 'An embargo should be set on the request.')

    def test_no_permission_to_edit(self):
        """Users without permission to edit the request should not be able to change the embargo"""
        user_without_permission = UserFactory(profile__acct_type='pro')
        assert_false(self.foia.has_perm(user_without_permission, 'change'))
        data = {'embargo': 'create'}
        request = self.request_factory.post(self.url, data)
        request.user = user_without_permission
        response = self.get_response(request)
        self.foia.refresh_from_db()
        eq_(response.status_code, 302)
        ok_(
            not self.foia.embargo,
            'The embargo should not be set on the request.'
        )

    def test_no_permission_to_embargo(self):
        """Users without permission to embargo the request should not be allowed to do so."""
        user_without_permission = UserFactory()
        self.foia.composer.user = user_without_permission
        self.foia.composer.save()
        ok_(self.foia.has_perm(user_without_permission, 'change'))
        assert_false(self.foia.has_perm(user_without_permission, 'embargo'))
        data = {'embargo': 'create'}
        request = self.request_factory.post(self.url, data)
        request.user = user_without_permission
        response = self.get_response(request)
        self.foia.refresh_from_db()
        eq_(response.status_code, 302)
        ok_(
            not self.foia.embargo,
            'The embargo should not be set on the request.'
        )

    def test_unembargo(self):
        """
        The embargo should be removable by editors of the request.
        Any user should be allowed to remove an embargo, even if they cannot apply one.
        """
        user_without_permission = UserFactory()
        self.foia.composer.user = user_without_permission
        self.foia.composer.save()
        self.foia.embargo = True
        self.foia.save()
        assert_true(self.foia.embargo)
        assert_true(self.foia.has_perm(user_without_permission, 'change'))
        assert_false(self.foia.has_perm(user_without_permission, 'embargo'))
        data = {'embargo': 'delete'}
        request = self.request_factory.post(self.url, data)
        request.user = user_without_permission
        response = self.get_response(request)
        self.foia.refresh_from_db()
        eq_(response.status_code, 302)
        assert_false(
            self.foia.embargo, 'The embargo should be removed from the request.'
        )

    def test_embargo_details(self):
        """
        If the request is in a closed state, it needs a date to be applied.
        If the user has permission, apply a permanent embargo.
        """
        self.foia.status = 'rejected'
        self.foia.save()
        default_expiration_date = datetime.date.today() + datetime.timedelta(1)
        embargo_form = FOIAEmbargoForm({
            'permanent_embargo': True,
            'date_embargo': default_expiration_date
        })
        assert_true(embargo_form.is_valid(), 'Form should validate.')
        assert_true(self.foia.has_perm(self.user, 'embargo_perm'))
        data = {'embargo': 'create'}
        data.update(embargo_form.data)
        request = self.request_factory.post(self.url, data)
        request.user = self.user
        response = self.get_response(request)
        self.foia.refresh_from_db()
        eq_(response.status_code, 302)
        assert_true(
            self.foia.embargo, 'An embargo should be set on the request.'
        )
        eq_(
            self.foia.date_embargo, default_expiration_date,
            'An expiration date should be set on the request.'
        )
        assert_true(
            self.foia.permanent_embargo,
            'A permanent embargo should be set on the request.'
        )

    def test_cannot_permanent_embargo(self):
        """Users who cannot set permanent embargoes shouldn't be able to."""
        user_without_permission = UserFactory(profile__acct_type='pro')
        self.foia.composer.user = user_without_permission
        self.foia.composer.save()
        assert_true(self.foia.has_perm(user_without_permission, 'embargo'))
        assert_false(
            self.foia.has_perm(user_without_permission, 'embargo_perm')
        )
        assert_true(self.foia.has_perm(user_without_permission, 'change'))
        embargo_form = FOIAEmbargoForm({'permanent_embargo': True})
        assert_true(embargo_form.is_valid(), 'Form should validate.')
        data = {'embargo': 'create'}
        data.update(embargo_form.data)
        request = self.request_factory.post(self.url, data)
        request.user = self.foia.composer.user
        response = self.get_response(request)
        self.foia.refresh_from_db()
        eq_(response.status_code, 302)
        assert_true(
            self.foia.embargo, 'An embargo should be set on the request.'
        )
        assert_false(
            self.foia.permanent_embargo,
            'A permanent embargo should not be set on the request.'
        )

    def test_update_embargo(self):
        """The embargo should be able to be updated."""
        self.foia.embargo = True
        self.foia.embargo_permanent = True
        self.foia.date_embargo = datetime.date.today() + datetime.timedelta(5)
        self.foia.status = 'rejected'
        self.foia.save()
        self.foia.refresh_from_db()
        assert_true(self.foia.embargo)
        expiration = datetime.date.today() + datetime.timedelta(15)
        embargo_form = FOIAEmbargoForm({'date_embargo': expiration})
        data = {'embargo': 'update'}
        data.update(embargo_form.data)
        request = self.request_factory.post(self.url, data)
        request.user = self.user
        response = self.get_response(request)
        eq_(response.status_code, 302)
        self.foia.refresh_from_db()
        assert_true(
            self.foia.embargo, 'The embargo should stay applied to the request.'
        )
        assert_false(
            self.foia.permanent_embargo,
            'The permanent embargo should be repealed.'
        )
        eq_(
            self.foia.date_embargo, expiration,
            'The embargo expiration date should be updated.'
        )

    def test_expire_embargo(self):
        """Any requests with an embargo date before today should be unembargoed"""
        self.foia.embargo = True
        self.foia.date_embargo = datetime.date.today() - datetime.timedelta(1)
        self.foia.status = 'rejected'
        self.foia.save()
        embargo_expire()
        self.foia.refresh_from_db()
        assert_false(self.foia.embargo, 'The embargo should be repealed.')

    def test_do_not_expire_permanent(self):
        """A request with a permanent embargo should stay embargoed."""
        self.foia.embargo = True
        self.foia.permanent_embargo = True
        self.foia.date_embargo = datetime.date.today() - datetime.timedelta(1)
        self.foia.status = 'rejected'
        self.foia.save()
        embargo_expire()
        self.foia.refresh_from_db()
        assert_true(self.foia.embargo, 'The embargo should remain embargoed.')

    def test_do_not_expire_no_date(self):
        """A request without an expiration date should not expire."""
        self.foia.embargo = True
        self.foia.save()
        embargo_expire()
        self.foia.refresh_from_db()
        assert_true(self.foia.embargo, 'The embargo should remain embargoed.')

    def test_expire_after_date(self):
        """Only after the date_embargo passes should the embargo expire."""
        self.foia.embargo = True
        self.foia.date_embargo = datetime.date.today()
        self.foia.status = 'rejected'
        self.foia.save()
        embargo_expire()
        self.foia.refresh_from_db()
        assert_true(self.foia.embargo, 'The embargo should remain embargoed.')

    def test_set_date_on_status_change(self):
        """
        If the request status is changed to an end status and it is embargoed,
        set the embargo expiration date to 30 days from today.
        """
        default_expiration_date = datetime.date.today() + datetime.timedelta(30)
        self.foia.embargo = True
        self.foia.save()
        self.foia.status = 'rejected'
        self.foia.save()
        self.foia.refresh_from_db()
        assert_true(self.foia.embargo and self.foia.status in END_STATUS)
        eq_(
            self.foia.date_embargo, default_expiration_date,
            'The embargo should be given an expiration date.'
        )

    def test_set_date_exception(self):
        """
        If the request is changed to an inactive state, it is embargoed, and there is no
        previously set expiration date, then set the embargo expiration to its default value.
        """
        extended_expiration_date = datetime.date.today(
        ) + datetime.timedelta(15)
        self.foia.embargo = True
        self.foia.date_embargo = extended_expiration_date
        self.foia.status = 'rejected'
        self.foia.save()
        self.foia.refresh_from_db()
        assert_true(self.foia.embargo and self.foia.status in END_STATUS)
        eq_(
            self.foia.date_embargo, extended_expiration_date,
            'The embargo should not change the extended expiration date.'
        )

    def test_remove_date(self):
        """The embargo date should be removed if the request is changed to an active state."""
        default_expiration_date = datetime.date.today() + datetime.timedelta(30)
        self.foia.embargo = True
        self.foia.save()
        self.foia.status = 'rejected'
        self.foia.save()
        self.foia.refresh_from_db()
        assert_true(self.foia.embargo and self.foia.status in END_STATUS)
        eq_(
            self.foia.date_embargo, default_expiration_date,
            'The embargo should be given an expiration date.'
        )
        self.foia.status = 'appealing'
        self.foia.save()
        self.foia.refresh_from_db()
        assert_false(self.foia.embargo and self.foia.status in END_STATUS)
        ok_(not self.foia.date_embargo, 'The embargo date should be removed.')
