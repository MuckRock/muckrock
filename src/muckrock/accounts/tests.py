"""
Tests using nose for the accounts application
"""

from django.forms import ValidationError
from django.contrib.auth.models import User
from django.test.client import Client
import nose.tools

from accounts.models import Profile
from accounts.templatetags.filters import format_phone
import accounts.forms

 # forms
def test_profile_form_zip():
    """Tests profile form zip code validation"""

    form = accounts.forms.ProfileForm()
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

def test_profile_form_phone():
    """Tests profile form zip code validation"""

    form = accounts.forms.ProfileForm()
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

def test_user_change_form_email():
    """Tests user change form email validation"""

    User.objects.create(username='test1', email='test1@muckrock.com')
    user2 = User.objects.create(username='test2', email='test2@muckrock.com')
    Profile.objects.create(user=user2)

    form = accounts.forms.UserChangeForm(instance=user2.get_profile())
    form.cleaned_data = {}
    form.cleaned_data['email'] = u'test2a@muckrock.com'
    nose.tools.eq_(form.clean_email(), u'test2a@muckrock.com', 'Non conflicting email')
    form.cleaned_data['email'] = u'test2a@muckrock.com'
    nose.tools.eq_(form.clean_email(), u'test2a@muckrock.com', 'Update without changing')
    form.cleaned_data['email'] = u'test1@muckrock.com'
    # conflicting email
    nose.tools.assert_raises(ValidationError, form.clean_email)

 # models
def test_profile_model_unicode():
    """Test profile model's __unicode__ method"""

    user3 = User.objects.create(username='test3', email='test3@muckrock.com')
    profile = Profile(user=user3)
    nose.tools.eq_(unicode(profile), u"Test3's Profile")

 # template filters
def test_format_phone():
    """Test the format phone template filter"""

    nose.tools.eq_(format_phone('5551234567'), '(555) 123-4567')

 # views
def test_views():
    """Test views and urls"""

    client = Client()

    def get_allowed(url, template):
        """Test a get on a url that is allowed with the users current credntials"""
        response = client.get(url)
        nose.tools.eq_(response.status_code, 200)
        nose.tools.eq_([t.name for t in response.template], [template, 'base.html'])

    def post_allowed(url, data, redirect):
        """Test an allowed post with the given data and redirect location"""
        response = client.post(url, data)
        nose.tools.eq_(response.status_code, 302)
        nose.tools.eq_(response['Location'], redirect)

    def post_allowed_bad(url, template):
        """Test an allowed post with bad data"""
        response = client.post(url, {'data': 'bad'})
        nose.tools.eq_(response.status_code, 200)
        nose.tools.eq_([t.name for t in response.template], [template, 'base.html'])

    def get_post_unallowed(url):
        """Test an unauthenticated get and post on a url that is allowed
        to be viewed only by authenticated users"""
        redirect = 'http://testserver/accounts/login/?next=' + url
        response = client.get(url)
        nose.tools.eq_(response.status_code, 302)
        nose.tools.eq_(response['Location'], redirect)

        response = client.put(url)
        nose.tools.eq_(response.status_code, 302)
        nose.tools.eq_(response['Location'], redirect)

    # get unathenticated pages
    get_allowed('/accounts/login/', 'registration/login.html')
    get_allowed('/accounts/register/', 'registration/register.html')
    get_allowed('/accounts/reset_pw/', 'registration/password_reset_form.html')
    get_allowed('/accounts/logout/', 'registration/logged_out.html')

    # get/post authenticated pages while unauthenticated
    get_post_unallowed('/accounts/profile/')
    get_post_unallowed('/accounts/update/')
    get_post_unallowed('/accounts/change_pw/')

    # post unathenticated pages
    post_allowed_bad('/accounts/register/', 'registration/register.html')

    # logs in for following tests
    post_allowed('/accounts/register/',
                 {'username': 'test4', 'password1': 'abc', 'password2': 'abc'},
                 'http://testserver/accounts/profile/')
    test_user = User.objects.get(username='test4')

    # get authenticated pages
    get_allowed('/accounts/profile/', 'registration/profile.html')
    get_allowed('/accounts/update/', 'registration/update.html')
    get_allowed('/accounts/change_pw/', 'registration/password_change_form.html')

    # post authenticated pages
    post_allowed_bad('/accounts/update/', 'registration/update.html')
    post_allowed_bad('/accounts/change_pw/', 'registration/password_change_form.html')

    user_data = {'first_name': 'mitchell',        'last_name': 'kotler',
                 'email': 'mitch@muckrock.com',   'user': test_user,
                 'address1': '123 main st',       'address2': '',
                 'city': 'boston', 'state': 'MA', 'zip_code': '02140',
                 'phone': '5551234567'}
    post_allowed('/accounts/update/', user_data, 'http://testserver/accounts/profile/')
    test_user = User.objects.get(username='test4')
    profile = test_user.get_profile()
    for key, val in user_data.iteritems():
        if key in ['first_name', 'last_name', 'email']:
            nose.tools.eq_(val, getattr(test_user, key))
        if key not in ['user', 'first_name', 'last_name', 'email']:
            nose.tools.eq_(val, getattr(profile, key))

    post_allowed('/accounts/change_pw/',
                {'old_password': 'abc',
                 'new_password1': '123',
                 'new_password2': '123'},
                 'http://testserver/accounts/change_pw_done/')

    # logout & check
    get_allowed('/accounts/logout/', 'registration/logged_out.html')
    get_post_unallowed('/accounts/profile/')

