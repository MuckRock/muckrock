"""
Tests using nose for the FOIA application
"""

from django.contrib.auth.models import User
from django.test.client import Client
from django.template.defaultfilters import slugify
from django.core.urlresolvers import reverse
from django.core import mail
import nose.tools

from datetime import datetime
from operator import attrgetter

from foia.models import FOIARequest, FOIAImage
from foia.forms import FOIARequestForm
from accounts.models import Profile
from muckrock.tests import get_allowed, post_allowed, post_allowed_bad, get_post_unallowed, get_404

def setup():
    """Clean the database before each test"""
    User.objects.all().delete()
    FOIARequest.objects.all().delete()
    FOIAImage.objects.all().delete()

    # clean the test mail outbox
    mail.outbox = []

 # forms
@nose.tools.with_setup(setup)
def test_foia_request_form_clean():
    """The form should prevent a user from having two requests with the same slug"""
    user1 = User.objects.create(username='test1', email='test1@muckrock.com')
    user2 = User.objects.create(username='test2', email='test2@muckrock.com')

    FOIARequest.objects.create(user=user1, title='test', slug='test', status='started',
                                       jurisdiction='massachusetts', agency='Clerk', request='test')
    foia2 = FOIARequest(user=user1)
    foia3 = FOIARequest(user=user2)

    foia_dict1 = {'title': 'test', 'slug': 'test', 'status': 'submitted',
                  'jurisdiction': 'massachusetts', 'agency': 'Clerk', 'request': 'abc'}
    foia_dict2 = {'title': 'new test', 'slug': 'new-test', 'status': 'submitted',
                  'jurisdiction': 'massachusetts', 'agency': 'Clerk', 'request': 'abc'}

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
    foia = FOIARequest.objects.create(user=user, jurisdiction='massachusetts',
                                      title='Test 1', slug='test-1')
    nose.tools.eq_(unicode(foia), u'Test 1')

@nose.tools.with_setup(setup)
def test_foia_model_url():
    """Test FOIA Request model's get_absolute_url method"""

    user = User.objects.create(username='Test_User')
    foia = FOIARequest.objects.create(user=user, jurisdiction='massachusetts', slug='Test-1')
    nose.tools.eq_(foia.get_absolute_url(),
        reverse('foia-detail', kwargs={'user_name': 'Test_User', 'slug': 'Test-1',
                                       'jurisdiction': 'massachusetts'}))

@nose.tools.with_setup(setup)
def test_foia_model_editable():
    """Test FOIA Request model's is_editable method"""

    user = User.objects.create(username='Test_User')

    def test(title, status, value):
        """Test the given status"""
        foia = FOIARequest.objects.create(user=user, title=title,
                                          jurisdiction='massachusetts',
                                          slug=slugify(title), status=status)
        nose.tools.eq_(foia.is_editable(), value)

    test('Test 1', 'started', True)
    test('Test 2', 'submitted', False)
    test('Test 3', 'fix', True)
    test('Test 4', 'rejected', False)
    test('Test 5', 'done', False)

@nose.tools.with_setup(setup)
def test_foia_doc_model_unicode():
    """Test FOIA Image model's __unicode__ method"""

    user = User.objects.create(username='Test_User')
    foia = FOIARequest.objects.create(user=user, title='Test 1', slug='test-1',
                                      jurisdiction='massachusetts')
    doc = FOIAImage.objects.create(foia=foia, page=1)
    nose.tools.eq_(unicode(doc), u'Test 1 Document Page 1')

@nose.tools.with_setup(setup)
def test_foia_doc_model_url():
    """Test FOIA Images model's get_absolute_url method"""

    user = User.objects.create(username='Test_User')
    foia = FOIARequest.objects.create(user=user, slug='Test-1', jurisdiction='massachusetts')
    doc = FOIAImage.objects.create(foia=foia, page=1)
    nose.tools.eq_(doc.get_absolute_url(),
        reverse('foia-doc-detail', kwargs={'user_name': 'Test_User', 'slug': 'Test-1', 'page': 1,
                                           'jurisdiction': 'massachusetts'}))

@nose.tools.with_setup(setup)
def test_foia_doc_next_prev():
    """Test FOIA Images model's next and previous methods"""

    user = User.objects.create(username='Test_User')
    foia = FOIARequest.objects.create(user=user, slug='Test-1', jurisdiction='massachusetts')
    doc1 = FOIAImage.objects.create(foia=foia, page=1)
    doc2 = FOIAImage.objects.create(foia=foia, page=2)
    doc3 = FOIAImage.objects.create(foia=foia, page=3)
    nose.tools.eq_(doc1.previous(), None)
    nose.tools.eq_(doc1.next(), doc2)
    nose.tools.eq_(doc2.previous(), doc1)
    nose.tools.eq_(doc2.next(), doc3)
    nose.tools.eq_(doc3.previous(), doc2)
    nose.tools.eq_(doc3.next(), None)

@nose.tools.with_setup(setup)
def test_foia_doc_total_pages():
    """Test FOIA Images model's total pages method"""

    user = User.objects.create(username='Test_User')
    foia = FOIARequest.objects.create(user=user, slug='Test-1', jurisdiction='massachusetts')
    doc1 = FOIAImage.objects.create(foia=foia, page=1)
    nose.tools.eq_(doc1.total_pages(), 1)

    doc2 = FOIAImage.objects.create(foia=foia, page=2)
    nose.tools.eq_(doc1.total_pages(), 2)
    nose.tools.eq_(doc2.total_pages(), 2)

    doc3 = FOIAImage.objects.create(foia=foia, page=3)
    nose.tools.eq_(doc1.total_pages(), 3)
    nose.tools.eq_(doc2.total_pages(), 3)
    nose.tools.eq_(doc3.total_pages(), 3)

@nose.tools.with_setup(setup)
def test_foia_email():
    """Test FOIA sending an email to the user when a FOIA request is saved"""

    nose.tools.eq_(len(mail.outbox), 0)

    user = User.objects.create(username='Test_User', email='user@test.com')
    foia = FOIARequest.objects.create(user=user, title='Test 1', slug='test-1', status='started',
                                      jurisdiction='massachusetts')

    nose.tools.eq_(len(mail.outbox), 1)
    nose.tools.eq_(mail.outbox[0].to, [user.email])

    foia.status = 'submitted'
    foia.save()

    nose.tools.eq_(len(mail.outbox), 2)

 # manager
@nose.tools.with_setup(setup)
def test_manager_get_submitted():
    """Test the FOIA Manager's get_submitted method"""
    user = User.objects.create(username='Test_User')

    foias = []
    foias.append(FOIARequest.objects.create(user=user, title='Test 1', slug='test-1',
                                            status='started', jurisdiction='massachusetts'))
    foias.append(FOIARequest.objects.create(user=user, title='Test 2', slug='test-2',
                                            status='submitted', jurisdiction='massachusetts'))
    foias.append(FOIARequest.objects.create(user=user, title='Test 3', slug='test-3',
                                            status='processed', jurisdiction='massachusetts'))
    foias.append(FOIARequest.objects.create(user=user, title='Test 4', slug='test-4',
                                            status='fix', jurisdiction='massachusetts'))
    foias.append(FOIARequest.objects.create(user=user, title='Test 5', slug='test-5',
                                            status='rejected', jurisdiction='massachusetts'))
    foias.append(FOIARequest.objects.create(user=user, title='Test 6', slug='test-6',
                                            status='done', jurisdiction='massachusetts'))

    nose.tools.eq_(set(FOIARequest.objects.get_submitted()), set(foias[1:]))

@nose.tools.with_setup(setup)
def test_manager_get_done():
    """Test the FOIA Manager's get_done method"""
    user = User.objects.create(username='Test_User')

    foias = []
    foias.append(FOIARequest.objects.create(user=user, title='Test 1', slug='test-1',
                                            status='started', jurisdiction='massachusetts'))
    foias.append(FOIARequest.objects.create(user=user, title='Test 2', slug='test-2',
                                            status='submitted', jurisdiction='massachusetts'))
    foias.append(FOIARequest.objects.create(user=user, title='Test 3', slug='test-3',
                                            status='processed', jurisdiction='massachusetts'))
    foias.append(FOIARequest.objects.create(user=user, title='Test 4', slug='test-4',
                                            status='fix', jurisdiction='massachusetts'))
    foias.append(FOIARequest.objects.create(user=user, title='Test 5', slug='test-5',
                                            status='rejected', jurisdiction='massachusetts'))
    foias.append(FOIARequest.objects.create(user=user, title='Test 6', slug='test-6',
                                            status='done', jurisdiction='massachusetts'))

    nose.tools.eq_(set(FOIARequest.objects.get_done()), set(foias[5:]))

 # views
@nose.tools.with_setup(setup)
def test_anon_views():
    """Test public views while not logged in"""

    client = Client()
    user1 = User.objects.create_user('test1', 'test1@muckrock.com', 'abc')
    user2 = User.objects.create_user('test2', 'test2@muckrock.com', 'abc')
    foia_a = FOIARequest.objects.create(user=user1, title='test a', slug='test-a', status='started',
                               jurisdiction='massachusetts', agency='Health', request='test')
    FOIARequest.objects.create(user=user1, title='test b', slug='test-b', status='done',
                               jurisdiction='boston-ma', agency='Finance', request='test')
    FOIARequest.objects.create(user=user2, title='test c', slug='test-c', status='rejected',
                               jurisdiction='cambridge-ma', agency='Clerk', request='test')
    doc1 = FOIAImage.objects.create(foia=foia_a, page=1)
    FOIAImage.objects.create(foia=foia_a, page=2)

    # get unathenticated pages
    response = get_allowed(client, reverse('foia-list'),
            ['foia/foiarequest_list.html', 'foia/base.html'])
    nose.tools.eq_(len(response.context['object_list']), 3)

    response = get_allowed(client, reverse('foia-list-user', kwargs={'user_name': 'test1'}),
                           ['foia/foiarequest_list.html', 'foia/base.html'])
    nose.tools.eq_(len(response.context['object_list']), 2)
    nose.tools.ok_(all(foia.user == user1 for foia in response.context['object_list']))

    response = get_allowed(client, reverse('foia-list-user', kwargs={'user_name': 'test2'}),
                           ['foia/foiarequest_list.html', 'foia/base.html'])
    nose.tools.eq_(len(response.context['object_list']), 1)
    nose.tools.ok_(all(foia.user == user2 for foia in response.context['object_list']))

    response = get_allowed(client, reverse('foia-sorted-list',
                           kwargs={'sort_order': 'asc', 'field': 'title'}),
                           ['foia/foiarequest_list.html', 'foia/base.html'])
    nose.tools.eq_(len(response.context['object_list']), 3)
    nose.tools.eq_([f.title for f in response.context['object_list']],
                   [f.title for f in sorted(response.context['object_list'],
                                            key=attrgetter('title'))])

    response = get_allowed(client, reverse('foia-sorted-list',
                           kwargs={'sort_order': 'desc', 'field': 'title'}),
                           ['foia/foiarequest_list.html', 'foia/base.html'])
    nose.tools.eq_(len(response.context['object_list']), 3)
    nose.tools.eq_([f.title for f in response.context['object_list']],
                   [f.title for f in sorted(response.context['object_list'],
                                            key=attrgetter('title'), reverse=True)])

    response = get_allowed(client, reverse('foia-sorted-list',
                           kwargs={'sort_order': 'asc', 'field': 'user'}),
                           ['foia/foiarequest_list.html', 'foia/base.html'])
    nose.tools.eq_(len(response.context['object_list']), 3)
    nose.tools.eq_([f.title for f in response.context['object_list']],
                   [f.title for f in sorted(response.context['object_list'],
                                            key=attrgetter('user.username'))])

    response = get_allowed(client, reverse('foia-sorted-list',
                           kwargs={'sort_order': 'desc', 'field': 'user'}),
                           ['foia/foiarequest_list.html', 'foia/base.html'])
    nose.tools.eq_(len(response.context['object_list']), 3)
    nose.tools.eq_([f.title for f in response.context['object_list']],
                   [f.title for f in sorted(response.context['object_list'],
                                            key=attrgetter('user.username'), reverse=True)])

    response = get_allowed(client, reverse('foia-sorted-list',
                           kwargs={'sort_order': 'asc', 'field': 'status'}),
                           ['foia/foiarequest_list.html', 'foia/base.html'])
    nose.tools.eq_(len(response.context['object_list']), 3)
    nose.tools.eq_([f.title for f in response.context['object_list']],
                   [f.title for f in sorted(response.context['object_list'],
                                            key=attrgetter('status'))])

    response = get_allowed(client, reverse('foia-sorted-list',
                           kwargs={'sort_order': 'desc', 'field': 'status'}),
                           ['foia/foiarequest_list.html', 'foia/base.html'])
    nose.tools.eq_(len(response.context['object_list']), 3)
    nose.tools.eq_([f.title for f in response.context['object_list']],
                   [f.title for f in sorted(response.context['object_list'],
                                            key=attrgetter('status'), reverse=True)])

    response = get_allowed(client, reverse('foia-sorted-list',
                           kwargs={'sort_order': 'asc', 'field': 'jurisdiction'}),
                           ['foia/foiarequest_list.html', 'foia/base.html'])
    nose.tools.eq_(len(response.context['object_list']), 3)
    nose.tools.eq_([f.title for f in response.context['object_list']],
                   [f.title for f in sorted(response.context['object_list'],
                                            key=attrgetter('jurisdiction'))])

    response = get_allowed(client, reverse('foia-sorted-list',
                           kwargs={'sort_order': 'desc', 'field': 'jurisdiction'}),
                           ['foia/foiarequest_list.html', 'foia/base.html'])
    nose.tools.eq_(len(response.context['object_list']), 3)
    nose.tools.eq_([f.title for f in response.context['object_list']],
                   [f.title for f in sorted(response.context['object_list'],
                                            key=attrgetter('jurisdiction'), reverse=True)])

    response = get_allowed(client,
                           reverse('foia-detail', kwargs={'user_name': 'test1', 'slug': 'test-a',
                                                          'jurisdiction': 'massachusetts'}),
                           ['foia/foiarequest_detail.html', 'foia/base.html'],
                           context = {'object': foia_a})

    response = get_allowed(client,
                           reverse('foia-doc-detail',
                               kwargs={'user_name': 'test1', 'slug': 'test-a', 'page': 1,
                                       'jurisdiction': 'massachusetts'}),
                           ['foia/foiarequest_doc_detail.html', 'foia/base.html'],
                           context = {'doc': doc1})

    response = get_allowed(client, reverse('foia-submitted-feed'))
    response = get_allowed(client, reverse('foia-done-feed'))

@nose.tools.with_setup(setup)
def test_404_views():
    """Test views that should give a 404 error"""

    client = Client()
    user1 = User.objects.create_user('test1', 'test1@muckrock.com', 'abc')
    user2 = User.objects.create_user('test2', 'test2@muckrock.com', 'abc')
    foia_a = FOIARequest.objects.create(user=user1, title='test a', slug='test-a', status='started',
                               jurisdiction='massachusetts', agency='Police', request='test')
    FOIARequest.objects.create(user=user1, title='test b', slug='test-b', status='done',
                               jurisdiction='boston-ma', agency='Health', request='test')
    FOIARequest.objects.create(user=user2, title='test c', slug='test-c', status='rejected',
                               jurisdiction='cambridge-ma', agency='Finance', request='test')
    FOIAImage.objects.create(foia=foia_a, page=1)
    FOIAImage.objects.create(foia=foia_a, page=2)

    get_404(client, reverse('foia-list-user', kwargs={'user_name': 'test3'}))
    get_404(client, reverse('foia-sorted-list', kwargs={'sort_order': 'asc', 'field': 'bad_field'}))
    get_404(client, reverse('foia-detail', kwargs={'user_name': 'test1', 'slug': 'test-c',
                                                   'jurisdiction': 'massachusetts'}))
    get_404(client, reverse('foia-detail', kwargs={'user_name': 'test3', 'slug': 'test-c',
                                                   'jurisdiction': 'massachusetts'}))
    get_404(client, reverse('foia-doc-detail',
                            kwargs={'user_name': 'test3', 'slug': 'test-c', 'page': 3,
                                    'jurisdiction': 'massachusetts'}))
    get_404(client, reverse('foia-doc-detail',
                            kwargs={'user_name': 'test2', 'slug': 'test-c', 'page': 1,
                                    'jurisdiction': 'massachusetts'}))
    get_404(client, reverse('foia-doc-detail',
                            kwargs={'user_name': 'test3', 'slug': 'test-c', 'page': 1,
                                    'jurisdiction': 'massachusetts'}))

@nose.tools.with_setup(setup)
def test_unallowed_views():
    """Test private views while not logged in"""

    client = Client()
    user = User.objects.create_user('test1', 'test1@muckrock.com', 'abc')
    FOIARequest.objects.create(user=user, title='test a', slug='test-a', status='started',
                               jurisdiction='massachusetts', agency='Clerk', request='test')

    # get/post authenticated pages while unauthenticated
    get_post_unallowed(client, reverse('foia-create'))
    get_post_unallowed(client, reverse('foia-update',
                                       kwargs={'jurisdiction': 'massachusetts',
                                               'user_name': 'test1', 'slug': 'test-a'}))

@nose.tools.with_setup(setup)
def test_auth_views():
    """Test private views while logged in"""

    client = Client()
    user = User.objects.create_user('test1', 'test1@muckrock.com', 'abc')
    Profile.objects.create(user=user, monthly_requests=10, date_update=datetime.now())
    FOIARequest.objects.create(user=user, title='test a', slug='test-a', status='started',
                               jurisdiction='massachusetts', agency='Clerk', request='test')
    client.login(username='test1', password='abc')

    # get authenticated pages
    get_allowed(client, reverse('foia-create'), ['foia/foiawizard_where.html', 'foia/base.html'])

    get_allowed(client, reverse('foia-update',
                                kwargs={'jurisdiction': 'massachusetts',
                                        'user_name': 'test1', 'slug': 'test-a'}),
                ['foia/foiarequest_form.html', 'foia/base.html'])

    get_404(client, reverse('foia-update',
                            kwargs={'jurisdiction': 'massachusetts',
                                    'user_name': 'test1', 'slug': 'test-b'}))

    # post authenticated pages
    post_allowed_bad(client, reverse('foia-create'),
                     ['foia/foiawizard_where.html', 'foia/base.html'])
    post_allowed_bad(client, reverse('foia-update',
                                     kwargs={'jurisdiction': 'massachusetts',
                                             'user_name': 'test1', 'slug': 'test-a'}),
                     ['foia/foiarequest_form.html', 'foia/base.html'])

@nose.tools.with_setup(setup)
def test_post_views():
    """Test posting data in views while logged in"""

    client = Client()
    user = User.objects.create_user('test1', 'test1@muckrock.com', 'abc')
    Profile.objects.create(user=user, monthly_requests=10, date_update=datetime.now())
    FOIARequest.objects.create(user=user, title='test a', slug='test-a', status='started',
                               jurisdiction='massachusetts', agency='Clerk', request='test')

    client.login(username='test1', password='abc')

    # test for submitting a foia request for enough credits
    # tests for the wizard

    foia_data = {'title': 'test a', 'jurisdiction': 'massachusetts',
                 'agency': 'Clerk', 'request': 'updated request', 'submit': 'Submit'}

    post_allowed(client, reverse('foia-update',
                                 kwargs={'jurisdiction': 'massachusetts',
                                         'user_name': 'test1', 'slug': 'test-a'}),
                 foia_data, 'http://testserver' +
                 reverse('foia-detail', kwargs={'user_name': 'test1', 'slug': 'test-a',
                                                'jurisdiction': 'massachusetts'}))
    foia = FOIARequest.objects.get(title='test a')
    nose.tools.eq_(foia.request, 'updated request')
    nose.tools.eq_(foia.status, 'submitted')
