"""
Tests using nose for the FOIA application
"""

from django.contrib.auth.models import User
from django.test.client import Client
from django.template.defaultfilters import slugify
import nose.tools

from foia.models import FOIARequest
from foia.forms import FOIARequestForm
from muckrock.tests import get_allowed, post_allowed, post_allowed_bad, get_post_unallowed, get_404

def setup():
    """Clean the database before each test"""
    User.objects.all().delete()
    FOIARequest.objects.all().delete()

 # forms
@nose.tools.with_setup(setup)
def test_foia_request_form_clean():
    """The form should prevent a user from having two requests with the same slug"""
    user1 = User.objects.create(username='test1', email='test1@muckrock.com')
    user2 = User.objects.create(username='test2', email='test2@muckrock.com')

    FOIARequest.objects.create(user=user1, title='test', slug='test', status='started',
                                       jurisdiction='MA', agency='test', request='test')
    foia2 = FOIARequest(user=user1)
    foia3 = FOIARequest(user=user2)

    foia_dict1 = {'title': 'test', 'slug': 'test', 'status': 'submitted',
                  'jurisdiction': 'MA', 'agency': 'abc', 'request': 'abc'}
    foia_dict2 = {'title': 'new test', 'slug': 'new-test', 'status': 'submitted',
                  'jurisdiction': 'MA', 'agency': 'abc', 'request': 'abc'}

    form = FOIARequestForm(foia_dict1, instance=foia2)
    nose.tools.assert_false(form.is_valid(),
                            'Form is not valid since user and slug are not unique together')

    form = FOIARequestForm(foia_dict2, instance=foia2)
    nose.tools.ok_(form.is_valid(),
                   'Form is valid since user and slug are unique together')

    form = FOIARequestForm(foia_dict1, instance=foia3)
    nose.tools.ok_(form.is_valid(),
                   'Form is valid since user and slug are unique together')
    #

 # models
@nose.tools.with_setup(setup)
def test_foia_model_unicode():
    """Test FOIA Request model's __unicode__ method"""

    user = User.objects.create(username='Test_User')
    foia = FOIARequest.objects.create(user=user, title='Test 1')
    nose.tools.eq_(unicode(foia), u'Test 1')

@nose.tools.with_setup(setup)
def test_foia_model_url():
    """Test FOIA Request model's get_absolute_url method"""

    user = User.objects.create(username='Test_User')
    foia = FOIARequest.objects.create(user=user, slug='Test-1')
    nose.tools.eq_(foia.get_absolute_url(), '/foia/view/Test_User/Test-1/')

@nose.tools.with_setup(setup)
def test_foia_model_editable():
    """Test FOIA Request model's is_editable method"""

    user = User.objects.create(username='Test_User')

    def test(title, status, value):
        """Test the given status"""
        foia = FOIARequest.objects.create(user=user, title=title,
                                          slug=slugify(title), status=status)
        nose.tools.eq_(foia.is_editable(), value)

    test('Test 1', 'started', True)
    test('Test 2', 'submitted', False)
    test('Test 3', 'fix', True)
    test('Test 4', 'rejected', False)
    test('Test 5', 'done', False)

 # views
@nose.tools.with_setup(setup)
def test_anon_views():
    """Test public views while not logged in"""

    client = Client()
    user1 = User.objects.create_user('test1', 'test1@muckrock.com', 'abc')
    user2 = User.objects.create_user('test2', 'test2@muckrock.com', 'abc')
    foia_a = FOIARequest.objects.create(user=user1, title='test a', slug='test-a', status='started',
                                        jurisdiction='MA', agency='test', request='test')
    FOIARequest.objects.create(user=user1, title='test b', slug='test-b', status='started',
                                        jurisdiction='MA', agency='test', request='test')
    FOIARequest.objects.create(user=user2, title='test c', slug='test-c', status='started',
                                        jurisdiction='MA', agency='test', request='test')

    # get unathenticated pages
    response = get_allowed(client, '/foia/list/', 'foia/foiarequest_list.html')
    nose.tools.eq_(len(response.context['object_list']), 3)

    response = get_allowed(client, '/foia/list/test1/', 'foia/foiarequest_list.html')
    nose.tools.eq_(len(response.context['object_list']), 2)
    nose.tools.ok_(all(foia.user == user1 for foia in response.context['object_list']))

    response = get_allowed(client, '/foia/list/test2/', 'foia/foiarequest_list.html')
    nose.tools.eq_(len(response.context['object_list']), 1)
    nose.tools.ok_(all(foia.user == user2 for foia in response.context['object_list']))

    response = get_allowed(client, '/foia/view/test1/test-a/', 'foia/foiarequest_detail.html',
                           context = {'object': foia_a})

    get_404(client, '/foia/list/test3/')
    get_404(client, '/foia/view/test1/test-c/')

@nose.tools.with_setup(setup)
def test_unallowed_views():
    """Test private views while not logged in"""

    client = Client()
    user = User.objects.create_user('test1', 'test1@muckrock.com', 'abc')
    FOIARequest.objects.create(user=user, title='test a', slug='test-a', status='started',
                               jurisdiction='MA', agency='test', request='test')

    # get/post authenticated pages while unauthenticated
    get_post_unallowed(client, '/foia/new/')
    get_post_unallowed(client, '/foia/update/test1/test-a/')

@nose.tools.with_setup(setup)
def test_auth_views():
    """Test private views while logged in"""

    client = Client()
    user = User.objects.create_user('test1', 'test1@muckrock.com', 'abc')
    FOIARequest.objects.create(user=user, title='test a', slug='test-a', status='started',
                               jurisdiction='MA', agency='test', request='test')
    client.login(username='test1', password='abc')

    # get authenticated pages
    get_allowed(client, '/foia/new/', 'foia/foiarequest_form.html')
    get_allowed(client, '/foia/update/test1/test-a/', 'foia/foiarequest_form.html')

    get_404(client, '/foia/update/test1/test-b/')

    # post authenticated pages
    post_allowed_bad(client, '/foia/new/', 'foia/foiarequest_form.html')
    post_allowed_bad(client, '/foia/update/test1/test-a/', 'foia/foiarequest_form.html')

@nose.tools.with_setup(setup)
def test_post_views():
    """Test posting data in views while logged in"""

    client = Client()
    user = User.objects.create_user('test1', 'test1@muckrock.com', 'abc')
    FOIARequest.objects.create(user=user, title='test a', slug='test-a', status='started',
                               jurisdiction='MA', agency='test', request='test')

    client.login(username='test1', password='abc')

    foia_data = {'title': 'test b', 'jurisdiction': 'MA',
                 'agency': 'test agency', 'request': 'test request', 'submit': 'Save'}

    post_allowed(client, '/foia/new/', foia_data, 'http://testserver/foia/view/test1/test-b/')
    foia = FOIARequest.objects.get(title='test b')
    nose.tools.eq_(foia.status, 'started')

    foia_data = {'title': 'test b', 'jurisdiction': 'MA',
                 'agency': 'test agency', 'request': 'updated request', 'submit': 'Submit'}

    post_allowed(client, '/foia/update/test1/test-b/', foia_data,
                 'http://testserver/foia/view/test1/test-b/')
    foia = FOIARequest.objects.get(title='test b')
    nose.tools.eq_(foia.request, 'updated request')
    nose.tools.eq_(foia.status, 'submitted')
