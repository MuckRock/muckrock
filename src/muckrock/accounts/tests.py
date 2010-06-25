"""
Tests using nose for the accounts application
"""

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.forms import ValidationError
from django.test.client import Client

import nose.tools
from datetime import datetime, timedelta

# this needs to be fully qualified for strange reasons
from muckrock.accounts.models import RequestLimitError
from accounts.models import Profile
from accounts.forms import UserChangeForm
from muckrock.tests import get_allowed, post_allowed, post_allowed_bad, get_post_unallowed
from settings import MONTHLY_REQUESTS

def setup():
    """Clean the database before each test"""
    User.objects.all().delete()
    Profile.objects.all().delete()

 # forms
@nose.tools.with_setup(setup)
def test_user_change_form_email():
    """Tests user change form email validation"""

    User.objects.create_user('test1', 'test1@muckrock.com', 'abc')
    user2 = User.objects.create(username='test2', email='tes21@muckrock.com')
    Profile.objects.create(user=user2, monthly_requests=10, date_update=datetime.now())

    form = UserChangeForm(instance=user2.get_profile())
    form.cleaned_data = {}
    form.cleaned_data['email'] = u'test2a@muckrock.com'
    nose.tools.eq_(form.clean_email(), u'test2a@muckrock.com', 'Non conflicting email')
    form.cleaned_data['email'] = u'test2a@muckrock.com'
    nose.tools.eq_(form.clean_email(), u'test2a@muckrock.com', 'Update without changing')
    form.cleaned_data['email'] = u'test1@muckrock.com'
    # conflicting email
    nose.tools.assert_raises(ValidationError, form.clean_email)

 # models
@nose.tools.with_setup(setup)
def test_profile_model_unicode():
    """Test profile model's __unicode__ method"""

    user = User.objects.create_user('test1', 'test1@muckrock.com', 'abc')
    profile = Profile(user=user, monthly_requests=10, date_update=datetime.now())
    nose.tools.eq_(unicode(profile), u"Test1's Profile")

@nose.tools.with_setup(setup)
def test_profile_get_num_requests():
    """Test profile model's get_num_request method"""

    user = User.objects.create_user('test1', 'test1@muckrock.com', 'abc')
    profile = Profile(user=user, monthly_requests=10, date_update=datetime.now())
    nose.tools.eq_(profile.get_num_requests(), 10)
    profile = Profile(user=user, monthly_requests=0,
                      date_update=datetime.now() - timedelta(days=32))
    nose.tools.eq_(profile.get_num_requests(), MONTHLY_REQUESTS)
    nose.tools.ok_(datetime.now() - profile.date_update < timedelta(minutes=5))

@nose.tools.with_setup(setup)
def test_profile_can_request():
    """Test profile model's can_request method"""

    user = User.objects.create_user('test1', 'test1@muckrock.com', 'abc')
    profile = Profile(user=user, monthly_requests=10, date_update=datetime.now())
    nose.tools.assert_true(profile.can_request())
    profile = Profile(user=user, monthly_requests=0,
                      date_update=datetime.now() - timedelta(days=32))
    nose.tools.assert_true(profile.can_request())
    profile = Profile(user=user, monthly_requests=0, date_update=datetime.now())
    nose.tools.assert_false(profile.can_request())

@nose.tools.with_setup(setup)
def test_profile_make_request():
    """Test profile model's make_request method"""

    user = User.objects.create_user('test1', 'test1@muckrock.com', 'abc')
    profile = Profile(user=user, monthly_requests=10, date_update=datetime.now())
    profile.make_request()
    nose.tools.eq_(profile.monthly_requests, 9)
    profile = Profile(user=user, monthly_requests=0, date_update=datetime.now())
    nose.tools.assert_raises(RequestLimitError, profile.make_request)

 # views
@nose.tools.with_setup(setup)
def test_anon_views():
    """Test public views while not logged in"""

    client = Client()
    User.objects.create_user('test1', 'test1@muckrock.com', 'abc')

    # get unathenticated pages
    get_allowed(client, reverse('acct-profile', args=['test1']),
                ['registration/profile.html', 'registration/base.html'])
    get_allowed(client, reverse('acct-login'),
                ['registration/login.html', 'registration/base.html'])
    get_allowed(client, reverse('acct-register'),
                ['registration/register.html', 'registration/base.html'])
    get_allowed(client, reverse('acct-reset-pw'),
                       ['registration/password_reset_form.html', 'registration/base.html'])
    get_allowed(client, reverse('acct-logout'),
                ['registration/logged_out.html', 'registration/base.html'])

@nose.tools.with_setup(setup)
def test_unallowed_views():
    """Test private views while not logged in"""

    client = Client()

    # get/post authenticated pages while unauthenticated
    get_post_unallowed(client, reverse('acct-my-profile'))
    get_post_unallowed(client, reverse('acct-update'))
    get_post_unallowed(client, reverse('acct-change-pw'))

    # post unathenticated pages
    post_allowed_bad(client, reverse('acct-register'),
                     ['registration/register.html', 'registration/base.html'])

@nose.tools.with_setup(setup)
def test_register_view():
    """Test the register view"""

    client = Client()

    post_allowed_bad(client, reverse('acct-register'),
                     ['registration/register.html', 'registration/base.html'])
    post_allowed(client, reverse('acct-register'),
                 {'username': 'test1', 'password1': 'abc', 'password2': 'abc'},
                 'http://testserver' + reverse('acct-my-profile'))

    # get authenticated pages
    get_allowed(client, reverse('acct-my-profile'),
                ['registration/profile.html', 'registration/base.html'])

@nose.tools.with_setup(setup)
def test_login_view():
    """Test the login view"""

    client = Client()
    User.objects.create_user('test1', 'test1@muckrock.com', 'abc')

    post_allowed_bad(client, reverse('acct-login'),
                     ['registration/login.html', 'registration/base.html'])
    post_allowed(client, reverse('acct-login'),
                 {'username': 'test1', 'password': 'abc'},
                 'http://testserver' + reverse('acct-my-profile'))

    # get authenticated pages
    get_allowed(client, reverse('acct-my-profile'),
                ['registration/profile.html', 'registration/base.html'])

@nose.tools.with_setup(setup)
def test_auth_views():
    """Test private views while logged in"""

    client = Client()
    user = User.objects.create_user('test1', 'test1@muckrock.com', 'abc')
    Profile.objects.create(user=user, monthly_requests=10, date_update=datetime.now())
    client.login(username='test1', password='abc')

    # get authenticated pages
    get_allowed(client, reverse('acct-my-profile'),
                ['registration/profile.html', 'registration/base.html'])
    get_allowed(client, reverse('acct-update'),
                ['registration/update.html', 'registration/base.html'])
    get_allowed(client, reverse('acct-change-pw'),
                ['registration/password_change_form.html', 'registration/base.html'])

    # post authenticated pages
    post_allowed_bad(client, reverse('acct-update'),
                     ['registration/update.html', 'registration/base.html'])
    post_allowed_bad(client, reverse('acct-change-pw'),
                     ['registration/password_change_form.html', 'registration/base.html'])

@nose.tools.with_setup(setup)
def test_post_views():
    """Test posting data in views while logged in"""

    client = Client()
    user = User.objects.create_user('test1', 'test1@muckrock.com', 'abc')
    Profile.objects.create(user=user, monthly_requests=10, date_update=datetime.now())
    client.login(username='test1', password='abc')

    user_data = {'first_name': 'mitchell',        'last_name': 'kotler',
                 'email': 'mitch@muckrock.com',   'user': user,
                 'address1': '123 main st',       'address2': '',
                 'city': 'boston', 'state': 'MA', 'zip_code': '02140',
                 'phone': '555-123-4567'}
    post_allowed(client, reverse('acct-update'), user_data,
        'http://testserver' + reverse('acct-my-profile'))

    user = User.objects.get(username='test1')
    profile = user.get_profile()
    for key, val in user_data.iteritems():
        if key in ['first_name', 'last_name', 'email']:
            nose.tools.eq_(val, getattr(user, key))
        if key not in ['user', 'first_name', 'last_name', 'email']:
            nose.tools.eq_(val, getattr(profile, key))

    post_allowed(client, reverse('acct-change-pw'),
                {'old_password': 'abc',
                 'new_password1': '123',
                 'new_password2': '123'},
                 'http://testserver' + reverse('acct-change-pw-done'))

@nose.tools.with_setup(setup)
def test_logout_view():
    """Test the logout view"""

    client = Client()
    user = User.objects.create_user('test1', 'test1@muckrock.com', 'abc')
    Profile.objects.create(user=user, monthly_requests=10, date_update=datetime.now())
    client.login(username='test1', password='abc')

    # logout & check
    get_allowed(client, reverse('acct-logout'),
                ['registration/logged_out.html', 'registration/base.html'])
    get_post_unallowed(client, reverse('acct-my-profile'))

