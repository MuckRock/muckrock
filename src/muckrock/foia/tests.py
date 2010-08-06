"""
Tests using nose for the FOIA application
"""

from django.contrib.auth.models import User, AnonymousUser
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core import mail
import nose.tools

from datetime import datetime, date, timedelta
from operator import attrgetter

from foia.models import FOIARequest, FOIAImage, Jurisdiction, AgencyType
from accounts.models import Profile
from muckrock.tests import get_allowed, post_allowed, post_allowed_bad, get_post_unallowed, get_404

# allow methods that could be functions and too many public methods in tests
# pylint: disable-msg=R0201
# pylint: disable-msg=R0904

class TestFOIAUnit(TestCase):
    """Unit tests for FOIA"""
    fixtures = ['jurisdictions.json', 'agency_types.json', 'test_users.json', 'test_foia.json']

    def setUp(self):
        """Set up tests"""
        # pylint: disable-msg=C0103
        self.foia = FOIARequest.objects.get(pk=1)

    # models
    def test_foia_model_unicode(self):
        """Test FOIA Request model's __unicode__ method"""
        nose.tools.eq_(unicode(self.foia), 'Test 1')

    def test_foia_model_url(self):
        """Test FOIA Request model's get_absolute_url method"""

        nose.tools.eq_(self.foia.get_absolute_url(),
            reverse('foia-detail', kwargs={'idx': self.foia.id, 'slug': 'test-1',
                                           'jurisdiction': 'massachusetts'}))

    def test_foia_model_editable(self):
        """Test FOIA Request model's is_editable method"""

        foias = FOIARequest.objects.all().order_by('id')[:5]
        for foia in foias[:5]:
            if foia.status in ['started', 'fix']:
                nose.tools.assert_true(foia.is_editable())
            else:
                nose.tools.assert_false(foia.is_editable())

    def test_foia_email(self):
        """Test FOIA sending an email to the user when a FOIA request is updated"""

        nose.tools.eq_(len(mail.outbox), 0)

        self.foia.status = 'submitted'
        self.foia.save()
        nose.tools.eq_(len(mail.outbox), 0)

        self.foia.status = 'processed'
        self.foia.save()
        nose.tools.eq_(len(mail.outbox), 1)
        nose.tools.eq_(mail.outbox[0].to, [self.foia.user.email])

        self.foia.status = 'fix'
        self.foia.save()
        nose.tools.eq_(len(mail.outbox), 2)

        self.foia.status = 'rejected'
        self.foia.save()
        nose.tools.eq_(len(mail.outbox), 3)

        self.foia.status = 'done'
        self.foia.save()
        nose.tools.eq_(len(mail.outbox), 4)

    def test_foia_viewable(self):
        """Test all the viewable and embargo functions"""

        user1 = User.objects.get(pk=1)
        user2 = User.objects.get(pk=2)

        foias = list(FOIARequest.objects.filter(id__in=[1, 5, 11, 12, 13, 14]).order_by('id'))
        foias[1].date_done = date.today() - timedelta(10)
        foias[2].date_done = date.today() - timedelta(10)
        foias[3].date_done = date.today() - timedelta(30)
        foias[4].date_done = date.today() - timedelta(90)

        # check manager get_viewable against models is_viewable
        viewable_foias = FOIARequest.objects.get_viewable(user1)
        for foia in FOIARequest.objects.all():
            if foia in viewable_foias:
                nose.tools.assert_true(foia.is_viewable(user1))
            else:
                nose.tools.assert_false(foia.is_viewable(user1))

        viewable_foias = FOIARequest.objects.get_viewable(user2)
        for foia in FOIARequest.objects.all():
            if foia in viewable_foias:
                nose.tools.assert_true(foia.is_viewable(user2))
            else:
                nose.tools.assert_false(foia.is_viewable(user2))

        viewable_foias = FOIARequest.objects.get_viewable(AnonymousUser())
        for foia in FOIARequest.objects.all():
            if foia in viewable_foias:
                nose.tools.assert_true(foia.is_viewable(AnonymousUser()))
            else:
                nose.tools.assert_false(foia.is_viewable(AnonymousUser()))

        nose.tools.assert_true(foias[0].is_viewable(user1))
        nose.tools.assert_true(foias[1].is_viewable(user1))
        nose.tools.assert_true(foias[2].is_viewable(user1))
        nose.tools.assert_true(foias[3].is_viewable(user1))
        nose.tools.assert_true(foias[4].is_viewable(user1))

        nose.tools.assert_false(foias[0].is_viewable(user2))
        nose.tools.assert_true (foias[1].is_viewable(user2))
        nose.tools.assert_false(foias[2].is_viewable(user2))
        nose.tools.assert_true (foias[3].is_viewable(user2))
        nose.tools.assert_true (foias[4].is_viewable(user2))

        nose.tools.assert_false(foias[0].is_viewable(AnonymousUser()))
        nose.tools.assert_true (foias[1].is_viewable(AnonymousUser()))
        nose.tools.assert_false(foias[2].is_viewable(AnonymousUser()))
        nose.tools.assert_true (foias[3].is_viewable(AnonymousUser()))
        nose.tools.assert_true (foias[4].is_viewable(AnonymousUser()))

    # Todo: Fix tests from here down
    def test_foia_doc_model_unicode(self):
        """Test FOIA Image model's __unicode__ method"""

        doc = FOIAImage.objects.create(foia=self.foia, page=1)
        nose.tools.eq_(unicode(doc), 'Test 1 Document Page 1')

    def test_foia_doc_model_url(self):
        """Test FOIA Images model's get_absolute_url method"""

        doc = FOIAImage.objects.create(foia=self.foia, page=1)
        nose.tools.eq_(doc.get_absolute_url(),
            reverse('foia-doc-detail', kwargs={'idx': self.foia.id, 'slug': 'test-1', 'page': 1,
                                               'jurisdiction': 'massachusetts'}))

    def test_foia_doc_next_prev(self):
        """Test FOIA Images model's next and previous methods"""

        doc1 = FOIAImage.objects.create(foia=self.foia, page=1)
        doc2 = FOIAImage.objects.create(foia=self.foia, page=2)
        doc3 = FOIAImage.objects.create(foia=self.foia, page=3)
        nose.tools.eq_(doc1.previous(), None)
        nose.tools.eq_(doc1.next(), doc2)
        nose.tools.eq_(doc2.previous(), doc1)
        nose.tools.eq_(doc2.next(), doc3)
        nose.tools.eq_(doc3.previous(), doc2)
        nose.tools.eq_(doc3.next(), None)

    def test_foia_doc_total_pages(self):
        """Test FOIA Images model's total pages method"""

        doc1 = FOIAImage.objects.create(foia=self.foia, page=1)
        nose.tools.eq_(doc1.total_pages(), 1)

        doc2 = FOIAImage.objects.create(foia=self.foia, page=2)
        nose.tools.eq_(doc1.total_pages(), 2)
        nose.tools.eq_(doc2.total_pages(), 2)

        doc3 = FOIAImage.objects.create(foia=self.foia, page=3)
        nose.tools.eq_(doc1.total_pages(), 3)
        nose.tools.eq_(doc2.total_pages(), 3)
        nose.tools.eq_(doc3.total_pages(), 3)

     # manager
    def test_manager_get_submitted(self):
        """Test the FOIA Manager's get_submitted method"""

        submitted_foias = FOIARequest.objects.get_submitted()
        for foia in FOIARequest.objects.all():
            if foia in submitted_foias:
                nose.tools.ok_(foia.status in ['submitted', 'processed', 'fix', 'rejected', 'done'])
            else:
                nose.tools.ok_(foia.status == 'started')

    def test_manager_get_done(self):
        """Test the FOIA Manager's get_done method"""

        done_foias = FOIARequest.objects.get_done()
        for foia in FOIARequest.objects.all():
            if foia in done_foias:
                nose.tools.ok_(foia.status == 'done')
            else:
                nose.tools.ok_(
                        foia.status in ['started', 'submitted', 'processed', 'fix', 'rejected'])


class TestFOIAFunctional(TestCase):
    """Functional tests for FOIA"""
    fixtures = ['jurisdictions.json', 'agency_types.json']

    # views
    def test_anon_views(self):
        """Test public views while not logged in"""

        user1 = User.objects.create_user('test1', 'test1@muckrock.com', 'abc')
        user2 = User.objects.create_user('test2', 'test2@muckrock.com', 'abc')
        FOIARequest.objects.create(user=user1, title='test a', slug='test-a', status='started',
                jurisdiction=Jurisdiction.objects.get(slug='massachusetts'),
                agency_type=AgencyType.objects.get(name='Health'), request='test')
        foia_b = FOIARequest.objects.create(user=user1, title='test b', slug='test-b',
                status='done', jurisdiction=Jurisdiction.objects.get(slug='boston-ma'),
                agency_type=AgencyType.objects.get(name='Finance'), request='test')
        FOIARequest.objects.create(user=user2, title='test c', slug='test-c', status='rejected',
                jurisdiction=Jurisdiction.objects.get(slug='cambridge-ma'),
                agency_type=AgencyType.objects.get(name='Clerk'), request='test')
        #doc1 = FOIAImage.objects.create(foia=foia_a, page=1)
        #FOIAImage.objects.create(foia=foia_a, page=2)

        # get unathenticated pages
        response = get_allowed(self.client, reverse('foia-list'),
                ['foia/foiarequest_list.html', 'foia/base.html'])
        # 2 because 'started' request is not viewable
        nose.tools.eq_(len(response.context['object_list']), 2)

        response = get_allowed(self.client,
                               reverse('foia-list-user', kwargs={'user_name': 'test1'}),
                               ['foia/foiarequest_list.html', 'foia/base.html'])
        # 1 because 'started' request is not viewable
        nose.tools.eq_(len(response.context['object_list']), 1)
        nose.tools.ok_(all(foia.user == user1 for foia in response.context['object_list']))

        response = get_allowed(self.client,
                               reverse('foia-list-user', kwargs={'user_name': 'test2'}),
                               ['foia/foiarequest_list.html', 'foia/base.html'])
        nose.tools.eq_(len(response.context['object_list']), 1)
        nose.tools.ok_(all(foia.user == user2 for foia in response.context['object_list']))

        response = get_allowed(self.client, reverse('foia-sorted-list',
                               kwargs={'sort_order': 'asc', 'field': 'title'}),
                               ['foia/foiarequest_list.html', 'foia/base.html'])
        # 2 because 'started' request is not viewable
        nose.tools.eq_(len(response.context['object_list']), 2)
        nose.tools.eq_([f.title for f in response.context['object_list']],
                       [f.title for f in sorted(response.context['object_list'],
                                                key=attrgetter('title'))])

        response = get_allowed(self.client, reverse('foia-sorted-list',
                               kwargs={'sort_order': 'desc', 'field': 'title'}),
                               ['foia/foiarequest_list.html', 'foia/base.html'])
        nose.tools.eq_(len(response.context['object_list']), 2)
        nose.tools.eq_([f.title for f in response.context['object_list']],
                       [f.title for f in sorted(response.context['object_list'],
                                                key=attrgetter('title'), reverse=True)])

        response = get_allowed(self.client, reverse('foia-sorted-list',
                               kwargs={'sort_order': 'asc', 'field': 'user'}),
                               ['foia/foiarequest_list.html', 'foia/base.html'])
        nose.tools.eq_(len(response.context['object_list']), 2)
        nose.tools.eq_([f.title for f in response.context['object_list']],
                       [f.title for f in sorted(response.context['object_list'],
                                                key=attrgetter('user.username'))])

        response = get_allowed(self.client, reverse('foia-sorted-list',
                               kwargs={'sort_order': 'desc', 'field': 'user'}),
                               ['foia/foiarequest_list.html', 'foia/base.html'])
        nose.tools.eq_(len(response.context['object_list']), 2)
        nose.tools.eq_([f.title for f in response.context['object_list']],
                       [f.title for f in sorted(response.context['object_list'],
                                                key=attrgetter('user.username'), reverse=True)])

        response = get_allowed(self.client, reverse('foia-sorted-list',
                               kwargs={'sort_order': 'asc', 'field': 'status'}),
                               ['foia/foiarequest_list.html', 'foia/base.html'])
        nose.tools.eq_(len(response.context['object_list']), 2)
        nose.tools.eq_([f.title for f in response.context['object_list']],
                       [f.title for f in sorted(response.context['object_list'],
                                                key=attrgetter('status'))])

        response = get_allowed(self.client, reverse('foia-sorted-list',
                               kwargs={'sort_order': 'desc', 'field': 'status'}),
                               ['foia/foiarequest_list.html', 'foia/base.html'])
        nose.tools.eq_(len(response.context['object_list']), 2)
        nose.tools.eq_([f.title for f in response.context['object_list']],
                       [f.title for f in sorted(response.context['object_list'],
                                                key=attrgetter('status'), reverse=True)])

        response = get_allowed(self.client, reverse('foia-sorted-list',
                               kwargs={'sort_order': 'asc', 'field': 'jurisdiction'}),
                               ['foia/foiarequest_list.html', 'foia/base.html'])
        nose.tools.eq_(len(response.context['object_list']), 2)
        nose.tools.eq_([f.title for f in response.context['object_list']],
                       [f.title for f in sorted(response.context['object_list'],
                                                key=attrgetter('jurisdiction.name'))])

        response = get_allowed(self.client, reverse('foia-sorted-list',
                               kwargs={'sort_order': 'desc', 'field': 'jurisdiction'}),
                               ['foia/foiarequest_list.html', 'foia/base.html'])
        nose.tools.eq_(len(response.context['object_list']), 2)
        nose.tools.eq_([f.title for f in response.context['object_list']],
                       [f.title for f in sorted(response.context['object_list'],
                                         key=attrgetter('jurisdiction.name'), reverse=True)])

        response = get_allowed(self.client,
                               reverse('foia-detail', kwargs={'idx': foia_b.id, 'slug': 'test-b',
                                                              'jurisdiction': 'boston-ma'}),
                               ['foia/foiarequest_detail.html', 'foia/base.html'],
                               context = {'object': foia_b})

        # Need a way to put an actual image in here for this to work
        #response = get_allowed(self.client,
        #                       reverse('foia-doc-detail',
        #                           kwargs={'user_name': 'test1', 'slug': 'test-a', 'page': 1,
        #                                   'jurisdiction': 'massachusetts'}),
        #                       ['foia/foiarequest_doc_detail.html', 'foia/base.html'],
        #                       context = {'doc': doc1})

        response = get_allowed(self.client, reverse('foia-submitted-feed'))
        response = get_allowed(self.client, reverse('foia-done-feed'))

    def test_404_views(self):
        """Test views that should give a 404 error"""

        user1 = User.objects.create_user('test1', 'test1@muckrock.com', 'abc')
        user2 = User.objects.create_user('test2', 'test2@muckrock.com', 'abc')
        foia_a = FOIARequest.objects.create(user=user1, title='test a', slug='test-a',
                status='started', jurisdiction=Jurisdiction.objects.get(slug='massachusetts'),
                agency_type=AgencyType.objects.get(name='Police'), request='test')
        FOIARequest.objects.create(user=user1, title='test b', slug='test-b', status='done',
                jurisdiction=Jurisdiction.objects.get(slug='boston-ma'),
                agency_type=AgencyType.objects.get(name='Health'), request='test')
        FOIARequest.objects.create(user=user2, title='test c', slug='test-c', status='rejected',
                jurisdiction=Jurisdiction.objects.get(slug='cambridge-ma'),
                agency_type=AgencyType.objects.get(name='Finance'), request='test')
        FOIAImage.objects.create(foia=foia_a, page=1)
        FOIAImage.objects.create(foia=foia_a, page=2)

        get_404(self.client, reverse('foia-list-user', kwargs={'user_name': 'test3'}))
        get_404(self.client, reverse('foia-sorted-list',
                kwargs={'sort_order': 'asc', 'field': 'bad_field'}))
        get_404(self.client, reverse('foia-detail', kwargs={'idx': 1, 'slug': 'test-c',
                                                       'jurisdiction': 'massachusetts'}))
        get_404(self.client, reverse('foia-detail', kwargs={'idx': 2, 'slug': 'test-c',
                                                       'jurisdiction': 'massachusetts'}))
        get_404(self.client, reverse('foia-doc-detail',
                                kwargs={'idx': 3, 'slug': 'test-c', 'page': 3,
                                        'jurisdiction': 'massachusetts'}))
        get_404(self.client, reverse('foia-doc-detail',
                                kwargs={'idx': 4, 'slug': 'test-c', 'page': 1,
                                        'jurisdiction': 'massachusetts'}))
        get_404(self.client, reverse('foia-doc-detail',
                                kwargs={'idx': 5, 'slug': 'test-c', 'page': 1,
                                        'jurisdiction': 'massachusetts'}))

    def test_unallowed_views(self):
        """Test private views while not logged in"""

        user = User.objects.create_user('test1', 'test1@muckrock.com', 'abc')
        foia = FOIARequest.objects.create(user=user, title='test a', slug='test-a',
                status='started', jurisdiction=Jurisdiction.objects.get(slug='massachusetts'),
                agency_type=AgencyType.objects.get(name='Clerk'), request='test')

        # get/post authenticated pages while unauthenticated
        get_post_unallowed(self.client, reverse('foia-create'))
        get_post_unallowed(self.client, reverse('foia-update',
                                           kwargs={'jurisdiction': 'massachusetts',
                                                   'idx': foia.id, 'slug': 'test-a'}))

    def test_auth_views(self):
        """Test private views while logged in"""

        user = User.objects.create_user('test1', 'test1@muckrock.com', 'abc')
        Profile.objects.create(user=user, monthly_requests=10, date_update=datetime.now())
        foia = FOIARequest.objects.create(user=user, title='test a', slug='test-a',
                status='started', jurisdiction=Jurisdiction.objects.get(slug='massachusetts'),
                agency_type=AgencyType.objects.get(name='Clerk'), request='test')
        self.client.login(username='test1', password='abc')

        # get authenticated pages
        get_allowed(self.client, reverse('foia-create'),
                    ['foia/foiawizard_where.html', 'foia/base-submit.html'])

        get_allowed(self.client, reverse('foia-update',
                                    kwargs={'jurisdiction': 'massachusetts',
                                            'idx': foia.id, 'slug': 'test-a'}),
                    ['foia/foiarequest_form.html', 'foia/base-submit.html'])

        get_404(self.client, reverse('foia-update',
                                kwargs={'jurisdiction': 'massachusetts',
                                        'idx': foia.id, 'slug': 'test-b'}))

        # post authenticated pages
        post_allowed_bad(self.client, reverse('foia-create'),
                         ['foia/foiawizard_where.html', 'foia/base-submit.html'])
        post_allowed_bad(self.client, reverse('foia-update',
                                         kwargs={'jurisdiction': 'massachusetts',
                                                 'idx': foia.id, 'slug': 'test-a'}),
                         ['foia/foiarequest_form.html', 'foia/base-submit.html'])

    def test_post_views(self):
        """Test posting data in views while logged in"""

        user = User.objects.create_user('test1', 'test1@muckrock.com', 'abc')
        Profile.objects.create(user=user, monthly_requests=10, date_update=datetime.now())
        foia = FOIARequest.objects.create(user=user, title='test a', slug='test-a',
                status='started', jurisdiction=Jurisdiction.objects.get(slug='massachusetts'),
                agency_type=AgencyType.objects.get(name='Clerk'), request='test')

        self.client.login(username='test1', password='abc')

        # test for submitting a foia request for enough credits
        # tests for the wizard

        foia_data = {'title': 'test a', 'request': 'updated request', 'submit': 'Submit',
                     'jurisdiction': Jurisdiction.objects.get(slug='massachusetts').pk,
                     'agency_type': AgencyType.objects.get(name='Clerk').pk}
                     

        post_allowed(self.client, reverse('foia-update',
                                     kwargs={'jurisdiction': 'massachusetts',
                                             'idx': foia.id, 'slug': 'test-a'}),
                     foia_data, 'http://testserver' +
                     reverse('foia-detail', kwargs={'idx': foia.id, 'slug': 'test-a',
                                                    'jurisdiction': 'massachusetts'}))
        foia = FOIARequest.objects.get(title='test a')
        nose.tools.eq_(foia.request, 'updated request')
        nose.tools.eq_(foia.status, 'submitted')
