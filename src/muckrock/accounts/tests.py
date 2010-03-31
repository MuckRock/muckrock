"""
Tests using nose for the accounts application
"""

from django.forms import ValidationError
from django.contrib.auth.models import User
from django.test.client import Client
import nose.tools

from accounts.models import Profile
from accounts.forms import ProfileForm, UserChangeForm
from accounts.templatetags.filters import format_phone
from muckrock.tests import get_allowed, post_allowed, post_allowed_bad, get_post_unallowed

def setup():
    """Clean the database before each test"""
    User.objects.all().delete()
    Profile.objects.all().delete()

 # forms
@nose.tools.with_setup(setup)
def test_profile_form_zip():
    """Tests profile form zip code validation"""

    form = ProfileForm()
    form.cleaned_data = {}
    form.cleaned_data['zip_code'] = u'01234'
    nose.tools.eq_(form.clean_zip_code(), u'01234', 'Good zip code should return unchanged')
    form.cleaned_data['zip_code'] = u'98765'
    nose.tools.eq_(form.clean_zip_code(), u'98765', 'Good zip code should return unchanged')
    # short zip code
    form.cleaned_data['zip_code'] = u'1234'
    nose.tools.assert_raises(ValidationError, form.clean_zip_code)
    # long zip code
    form.cleaned_data['zip_code'] = u'012345'
    nose.tools.assert_raises(ValidationError, form.clean_zip_code)
    # bad digits zip code
    form.cleaned_data['zip_code'] = u'01a23'
    nose.tools.assert_raises(ValidationError, form.clean_zip_code)

@nose.tools.with_setup(setup)
def test_profile_form_phone():
    """Tests profile form zip code validation"""

    form = ProfileForm()
    form.cleaned_data = {}
    form.cleaned_data['phone'] = u'5551234567'
    nose.tools.eq_(form.clean_phone(), u'5551234567', 'Simple phone number')
    form.cleaned_data['phone'] = u'555-123-4567'
    nose.tools.eq_(form.clean_phone(), u'5551234567', 'Phone with punctuation')
    form.cleaned_data['phone'] = u'(555) 123-4567'
    nose.tools.eq_(form.clean_phone(), u'5551234567', 'Phone with punctuation and white space')
    form.cleaned_data['phone'] = u'1 (555) 123-4567'
    nose.tools.eq_(form.clean_phone(), u'5551234567', 'Phone with leading one')
    # short phone
    form.cleaned_data['phone'] = u'1234567890'
    nose.tools.assert_raises(ValidationError, form.clean_phone)
    form.cleaned_data['phone'] = u'(234) 567-890'
    nose.tools.assert_raises(ValidationError, form.clean_phone)
    # long phone
    form.cleaned_data['phone'] = u'(234) 567-89011'
    nose.tools.assert_raises(ValidationError, form.clean_phone)
    # bad phone
    form.cleaned_data['phone'] = u'1 (800) CALL-ATT'
    nose.tools.assert_raises(ValidationError, form.clean_phone)

@nose.tools.with_setup(setup)
def test_user_change_form_email():
    """Tests user change form email validation"""

    User.objects.create_user('test1', 'test1@muckrock.com', 'abc')
    user2 = User.objects.create(username='test2', email='tes21@muckrock.com')
    Profile.objects.create(user=user2)

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
    profile = Profile(user=user)
    nose.tools.eq_(unicode(profile), u"Test1's Profile")

 # template filters
@nose.tools.with_setup(setup)
def test_format_phone():
    """Test the format phone template filter"""

    nose.tools.eq_(format_phone('5551234567'), '(555) 123-4567')

 # views
@nose.tools.with_setup(setup)
def test_anon_views():
    """Test public views while not logged in"""

    client = Client()

    # get unathenticated pages
    get_allowed(client, '/accounts/login/', ['registration/login.html', 'registration/base.html'])
    get_allowed(client, '/accounts/register/',
                ['registration/register.html', 'registration/base.html'])
    get_allowed(client, '/accounts/reset_pw/',
                       ['registration/password_reset_form.html', 'registration/base.html'])
    get_allowed(client, '/accounts/logout/',
                ['registration/logged_out.html', 'registration/base.html'])

@nose.tools.with_setup(setup)
def test_unallowed_views():
    """Test private views while not logged in"""

    client = Client()

    # get/post authenticated pages while unauthenticated
    get_post_unallowed(client, '/accounts/profile/')
    get_post_unallowed(client, '/accounts/update/')
    get_post_unallowed(client, '/accounts/change_pw/')

    # post unathenticated pages
    post_allowed_bad(client, '/accounts/register/',
                     ['registration/register.html', 'registration/base.html'])

@nose.tools.with_setup(setup)
def test_register_view():
    """Test the register view"""

    client = Client()

    post_allowed_bad(client, '/accounts/register/',
                     ['registration/register.html', 'registration/base.html'])
    post_allowed(client, '/accounts/register/',
                 {'username': 'test1', 'password1': 'abc', 'password2': 'abc'},
                 'http://testserver/accounts/profile/')

    # get authenticated pages
    get_allowed(client, '/accounts/profile/',
                ['registration/profile.html', 'registration/base.html'])

@nose.tools.with_setup(setup)
def test_login_view():
    """Test the login view"""

    client = Client()
    User.objects.create_user('test1', 'test1@muckrock.com', 'abc')

    post_allowed_bad(client, '/accounts/login/',
                     ['registration/login.html', 'registration/base.html'])
    post_allowed(client, '/accounts/login/',
                 {'username': 'test1', 'password': 'abc'},
                 'http://testserver/accounts/profile/')

    # get authenticated pages
    get_allowed(client, '/accounts/profile/',
                ['registration/profile.html', 'registration/base.html'])

@nose.tools.with_setup(setup)
def test_auth_views():
    """Test private views while logged in"""

    client = Client()
    User.objects.create_user('test1', 'test1@muckrock.com', 'abc')
    client.login(username='test1', password='abc')

    # get authenticated pages
    get_allowed(client, '/accounts/profile/',
                ['registration/profile.html', 'registration/base.html'])
    get_allowed(client, '/accounts/update/',
                ['registration/update.html', 'registration/base.html'])
    get_allowed(client, '/accounts/change_pw/',
                ['registration/password_change_form.html', 'registration/base.html'])

    # post authenticated pages
    post_allowed_bad(client, '/accounts/update/',
                     ['registration/update.html', 'registration/base.html'])
    post_allowed_bad(client, '/accounts/change_pw/',
                     ['registration/password_change_form.html', 'registration/base.html'])

@nose.tools.with_setup(setup)
def test_post_views():
    """Test posting data in views while logged in"""

    client = Client()
    user = User.objects.create_user('test1', 'test1@muckrock.com', 'abc')
    client.login(username='test1', password='abc')

    user_data = {'first_name': 'mitchell',        'last_name': 'kotler',
                 'email': 'mitch@muckrock.com',   'user': user,
                 'address1': '123 main st',       'address2': '',
                 'city': 'boston', 'state': 'MA', 'zip_code': '02140',
                 'phone': '5551234567'}
    post_allowed(client, '/accounts/update/', user_data, 'http://testserver/accounts/profile/')

    user = User.objects.get(username='test1')
    profile = user.get_profile()
    for key, val in user_data.iteritems():
        if key in ['first_name', 'last_name', 'email']:
            nose.tools.eq_(val, getattr(user, key))
        if key not in ['user', 'first_name', 'last_name', 'email']:
            nose.tools.eq_(val, getattr(profile, key))

    post_allowed(client, '/accounts/change_pw/',
                {'old_password': 'abc',
                 'new_password1': '123',
                 'new_password2': '123'},
                 'http://testserver/accounts/change_pw_done/')

@nose.tools.with_setup(setup)
def test_logout_view():
    """Test the logout view"""

    client = Client()
    User.objects.create_user('test1', 'test1@muckrock.com', 'abc')
    client.login(username='test1', password='abc')

    # logout & check
    get_allowed(client, '/accounts/logout/',
                ['registration/logged_out.html', 'registration/base.html'])
    get_post_unallowed(client, '/accounts/profile/')

