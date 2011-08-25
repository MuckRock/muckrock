"""
Tests using nose for the accounts application
"""

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.forms import ValidationError
from django.test import TestCase

import nose.tools
from datetime import datetime, timedelta

from accounts.models import Profile
from accounts.forms import UserChangeForm, UserCreationForm
from muckrock.tests import get_allowed, post_allowed, post_allowed_bad, get_post_unallowed
from settings import MONTHLY_REQUESTS

# allow long names, methods that could be functions and too many public methods in tests
# pylint: disable-msg=C0103
# pylint: disable-msg=R0201
# pylint: disable-msg=R0904

class TestAccountUnit(TestCase):
    """Unit tests for account"""
    fixtures = ['test_users.json', 'test_profiles.json']

    def setUp(self):
        """Set up tests"""
        self.profile = Profile.objects.get(pk=1)

    # forms
    def test_user_change_form_email_normal(self):
        """Changing email normally should succeed"""
        # pylint: disable-msg=W0201
        form = UserChangeForm(instance=self.profile)
        form.cleaned_data = {}
        form.cleaned_data['email'] = 'new@example.com'
        nose.tools.eq_(form.clean_email(), 'new@example.com')

    def test_user_change_form_email_same(self):
        """Keeping email the same should succeed"""
        form = UserChangeForm(instance=self.profile)
        form.cleaned_data = {}
        form.cleaned_data['email'] = 'adam@example.com'
        nose.tools.eq_(form.clean_email(), 'adam@example.com')

    def test_user_change_form_email_conflict(self):
        """Trying to use an already taken email should fail"""
        form = UserChangeForm(instance=self.profile)
        form.cleaned_data = {}
        form.cleaned_data['email'] = 'bob@example.com'
        nose.tools.assert_raises(ValidationError, form.clean_email) # conflicting email

    def test_user_creation_form(self):
        """Create a new user - name should be case insensitive"""
        form = UserCreationForm()
        form.cleaned_data = {}
        form.cleaned_data['username'] = 'ADAM'
        nose.tools.assert_raises(ValidationError, form.clean_username) # conflicting name

    # models
    def test_profile_model_unicode(self):
        """Test profile model's __unicode__ method"""
        nose.tools.eq_(unicode(self.profile), "Adam's Profile", 'Profile unicode method')

    def test_profile_get_monthly_requests(self):
        """Normal get number reuqests just returns the current value"""
        profile = Profile.objects.get(pk=2)
        profile.date_update = datetime.now()
        nose.tools.eq_(profile.get_monthly_requests(), 10, 'normal get num requests')

    def test_profile_get_monthly_requests_refresh(self):
        """Get number requests resets the number of requests if its been over a month"""
        profile = Profile.objects.get(pk=2)
        profile.date_update = datetime.now() - timedelta(32)
        nose.tools.eq_(profile.get_monthly_requests(), MONTHLY_REQUESTS[profile.acct_type])
        nose.tools.ok_(datetime.now() - profile.date_update < timedelta(minutes=5))

    def test_profile_make_request_refresh(self):
        """Make request resets count if it has been more than a month"""
        profile = Profile.objects.get(pk=3)
        profile.date_update = datetime.now() - timedelta(32)
        nose.tools.assert_true(profile.make_request())

    def test_profile_make_request_pass(self):
        """Normal make request call decrements number of requests"""
        self.profile.date_update = datetime.now()
        self.profile.make_request()
        nose.tools.eq_(self.profile.monthly_requests, 24)

    def test_profile_make_request_fail(self):
        """If out of requests, make request returns false"""
        profile = Profile.objects.get(pk=3)
        profile.date_update = datetime.now()
        nose.tools.assert_false(profile.make_request())


class TestAccountFunctional(TestCase):
    """Functional tests for account"""
    fixtures = ['test_users.json', 'test_profiles.json', 'test_statistics.json']

    # views
    def test_anon_views(self):
        """Test public views while not logged in"""

        urls_and_templates = [
                (reverse('acct-profile', args=['adam']), 'registration/profile.html'),
                (reverse('acct-login'),                  'registration/login.html'),
                (reverse('acct-register'),               'registration/register.html'),
                (reverse('acct-reset-pw'),               'registration/password_reset_form.html'),
                (reverse('acct-logout'),                 'registration/logged_out.html'),
                ]

        for url, template in urls_and_templates:
            get_allowed(self.client, url, [template, 'registration/base.html'])

    def test_unallowed_views(self):
        """Test private views while not logged in"""

        # get/post authenticated pages while unauthenticated
        url_names = ['acct-my-profile', 'acct-update', 'acct-change-pw']
        for url_name in url_names:
            get_post_unallowed(self.client, reverse(url_name))

        # post unathenticated pages
        post_allowed_bad(self.client, reverse('acct-register'),
                         ['registration/register.html', 'registration/base.html'])

    def test_register_view(self):
        """Test the register view"""

        post_allowed_bad(self.client, reverse('acct-register'),
                         ['registration/register.html', 'registration/base.html'])
        post_allowed(self.client, reverse('acct-register'),
                     {'username': 'test1', 'password1': 'abc', 'password2': 'abc'},
                     'http://testserver' + reverse('acct-my-profile'))

        # get authenticated pages
        get_allowed(self.client, reverse('acct-my-profile'),
                    ['registration/profile.html', 'registration/base.html'])

    def test_login_view(self):
        """Test the login view"""

        post_allowed_bad(self.client, reverse('acct-login'),
                         ['registration/login.html', 'registration/base.html'])
        post_allowed(self.client, reverse('acct-login'),
                     {'username': 'adam', 'password': 'abc'},
                     'http://testserver' + reverse('acct-my-profile'))

        # get authenticated pages
        get_allowed(self.client, reverse('acct-my-profile'),
                    ['registration/profile.html', 'registration/base.html'])

    def test_auth_views(self):
        """Test private views while logged in"""

        self.client.login(username='adam', password='abc')

        # get authenticated pages
        urls_and_templates = [
                ('acct-my-profile', 'registration/profile.html'),
                ('acct-update',     'registration/update.html'),
                ('acct-change-pw',  'registration/password_change_form.html'),
                ]

        for url_name, template in urls_and_templates:
            get_allowed(self.client, reverse(url_name), [template, 'registration/base.html'])

        # post authenticated pages
        post_allowed_bad(self.client, reverse('acct-update'),
                         ['registration/update.html', 'registration/base.html'])
        post_allowed_bad(self.client, reverse('acct-change-pw'),
                         ['registration/password_change_form.html', 'registration/base.html'])

    def test_post_views(self):
        """Test posting data in views while logged in"""

        self.client.login(username='adam', password='abc')
        user = User.objects.get(username='adam')

        user_data = {'first_name': 'mitchell',        'last_name': 'kotler',
                     'email': 'mitch@muckrock.com',   'user': user,
                     'address1': '123 main st',       'address2': '',
                     'city': 'boston', 'state': 'MA', 'zip_code': '02140',
                     'phone': '555-123-4567'}
        post_allowed(self.client, reverse('acct-update'), user_data,
            'http://testserver' + reverse('acct-my-profile'))

        user = User.objects.get(username='adam')
        profile = user.get_profile()
        for key, val in user_data.iteritems():
            if key in ['first_name', 'last_name', 'email']:
                nose.tools.eq_(val, getattr(user, key))
            if key not in ['user', 'first_name', 'last_name', 'email']:
                nose.tools.eq_(val, getattr(profile, key))

        post_allowed(self.client, reverse('acct-change-pw'),
                    {'old_password': 'abc',
                     'new_password1': '123',
                     'new_password2': '123'},
                     'http://testserver' + reverse('acct-change-pw-done'))

    def test_logout_view(self):
        """Test the logout view"""

        self.client.login(username='adam', password='abc')

        # logout & check
        get_allowed(self.client, reverse('acct-logout'),
                    ['registration/logged_out.html', 'registration/base.html'])
        get_post_unallowed(self.client, reverse('acct-my-profile'))

    def test_admin_views(self):
        """Test additional admin views"""

        self.client.login(username='adam', password='abc')
        response = get_allowed(self.client, reverse('admin:stats-csv'))
        nose.tools.eq_(response['content-type'], 'text/csv')

