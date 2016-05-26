"""
Tests using nose for the FOIA application
"""

from django.contrib.auth.models import User, AnonymousUser
from django.core.urlresolvers import reverse
from django.core import mail
from django.http import Http404
from django.test import TestCase, RequestFactory

import datetime
from datetime import date as real_date
from mock import Mock, patch
import nose.tools
from operator import attrgetter
import re

from muckrock.accounts.models import Profile
from muckrock.agency.models import Agency
from muckrock.factories import UserFactory, FOIARequestFactory, FOIAFileFactory, ProjectFactory
from muckrock.foia.models import FOIARequest, FOIACommunication
from muckrock.foia.views import Detail, FOIAFileListView
from muckrock.foia.views.composers import _make_user
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.project.forms import ProjectManagerForm
from muckrock.task.models import SnailMailTask
from muckrock.tests import get_allowed, post_allowed, get_post_unallowed, get_404
from muckrock.utils import mock_middleware

ok_ = nose.tools.ok_
eq_ = nose.tools.eq_
raises = nose.tools.raises

# allow methods that could be functions and too many public methods in tests
# pylint: disable=no-self-use
# pylint: disable=too-many-public-methods
# pylint: disable=too-many-lines
# pylint: disable=invalid-name
# pylint: disable=bad-mcs-method-argument

class TestFOIARequestUnit(TestCase):
    """Unit tests for FOIARequests"""
    fixtures = ['holidays.json', 'jurisdictions.json', 'agency_types.json', 'test_users.json',
                'test_agencies.json', 'test_profiles.json', 'test_foiarequests.json',
                'test_foiacommunications.json']

    def setUp(self):
        """Set up tests"""

        mail.outbox = []

        self.foia = FOIARequest.objects.get(pk=1)

    # models
    def test_foia_model_unicode(self):
        """Test FOIA Request model's __unicode__ method"""
        nose.tools.eq_(unicode(self.foia), 'Test 1')

    def test_foia_model_url(self):
        """Test FOIA Request model's get_absolute_url method"""

        nose.tools.eq_(self.foia.get_absolute_url(),
            reverse('foia-detail', kwargs={'idx': self.foia.pk, 'slug': 'test-1',
                                           'jurisdiction': 'massachusetts',
                                           'jidx': self.foia.jurisdiction.pk}))

    def test_foia_model_editable(self):
        """Test FOIA Request model's is_editable method"""

        foias = FOIARequest.objects.all().order_by('id')[:5]
        for foia in foias[:5]:
            if foia.status in ['started']:
                nose.tools.assert_true(foia.is_editable())
            else:
                nose.tools.assert_false(foia.is_editable())

    def test_foia_viewable(self):
        """Test all the viewable and embargo functions"""

        user1 = User.objects.get(pk=1)
        user2 = User.objects.get(pk=2)

        foias = list(FOIARequest.objects.filter(id__in=[1, 5, 11, 12, 13, 14]).order_by('id'))
        # 0 = draft
        # 1 = completed, no embargo
        # 2 = completed, embargoed, no expiration
        # 3 = completed, embargoed, no expiration
        # 4 = completed, embargoed, no expiration
        foias[1].date_embargo = datetime.date.today() + datetime.timedelta(10)
        foias[2].date_embargo = datetime.date.today()
        foias[3].date_embargo = datetime.date.today() - datetime.timedelta(1)
        foias[3].embargo = False
        foias[4].date_embargo = datetime.date.today() - datetime.timedelta(10)
        foias[4].embargo = False

        # check manager get_viewable against models viewable_by
        viewable_foias = FOIARequest.objects.get_viewable(user1)
        for foia in FOIARequest.objects.all():
            if foia in viewable_foias:
                nose.tools.assert_true(foia.viewable_by(user1))
            else:
                nose.tools.assert_false(foia.viewable_by(user1))

        viewable_foias = FOIARequest.objects.get_viewable(user2)
        for foia in FOIARequest.objects.all():
            if foia in viewable_foias:
                nose.tools.assert_true(foia.viewable_by(user2))
            else:
                nose.tools.assert_false(foia.viewable_by(user2))

        viewable_foias = FOIARequest.objects.get_public()
        for foia in FOIARequest.objects.all():
            if foia in viewable_foias:
                nose.tools.assert_true(foia.viewable_by(AnonymousUser()))
            else:
                nose.tools.assert_false(foia.viewable_by(AnonymousUser()))

        nose.tools.assert_true(foias[0].viewable_by(user1))
        nose.tools.assert_true(foias[1].viewable_by(user1))
        nose.tools.assert_true(foias[2].viewable_by(user1))
        nose.tools.assert_true(foias[3].viewable_by(user1))
        nose.tools.assert_true(foias[4].viewable_by(user1))

        nose.tools.assert_false(foias[0].viewable_by(user2))
        nose.tools.assert_true(foias[1].viewable_by(user2))
        nose.tools.assert_false(foias[2].viewable_by(user2))
        nose.tools.assert_true(foias[3].viewable_by(user2))
        nose.tools.assert_true(foias[4].viewable_by(user2))

        nose.tools.assert_false(foias[0].viewable_by(AnonymousUser()))
        nose.tools.assert_true(foias[1].viewable_by(AnonymousUser()))
        nose.tools.assert_false(foias[2].viewable_by(AnonymousUser()))
        nose.tools.assert_true(foias[3].viewable_by(AnonymousUser()))
        nose.tools.assert_true(foias[4].viewable_by(AnonymousUser()))

    def test_foia_set_mail_id(self):
        """Test the set_mail_id function"""
        foia = FOIARequest.objects.get(pk=17)
        foia.set_mail_id()
        mail_id = foia.mail_id
        nose.tools.ok_(re.match(r'\d{1,4}-\d{8}', mail_id))

        foia.set_mail_id()
        nose.tools.eq_(mail_id, foia.mail_id)

    def test_foia_followup(self):
        """Make sure the follow up date is set correctly"""
        # pylint: disable=protected-access
        foia = FOIARequest.objects.get(pk=15)
        foia.followup()
        nose.tools.assert_in('I can expect', mail.outbox[-1].body)
        nose.tools.eq_(foia.date_followup,
                       datetime.date.today() + datetime.timedelta(foia._followup_days()))

        nose.tools.eq_(foia._followup_days(), 15)

        num_days = 365
        foia.date_estimate = datetime.date.today() + datetime.timedelta(num_days)
        foia.followup(automatic=True)
        nose.tools.assert_in('I am still', mail.outbox[-1].body)
        nose.tools.eq_(foia._followup_days(), num_days)

        foia.date_estimate = datetime.date.today()
        foia.followup()
        nose.tools.assert_in('check on the status', mail.outbox[-1].body)
        nose.tools.eq_(foia._followup_days(), 15)

    def test_foia_followup_estimated(self):
        """If request has an estimated date, returns number of days until the estimated date"""
        # pylint: disable=protected-access
        num_days = 365
        foia = FOIARequest.objects.get(pk=15)
        foia.date_estimate = datetime.date.today() + datetime.timedelta(num_days)
        nose.tools.eq_(foia._followup_days(), num_days)

     # manager
    def test_manager_get_submitted(self):
        """Test the FOIA Manager's get_submitted method"""

        submitted_foias = FOIARequest.objects.get_submitted()
        for foia in FOIARequest.objects.all():
            if foia in submitted_foias:
                nose.tools.ok_(foia.status != 'started')
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
                        foia.status in ['started', 'submitted', 'processed',
                                        'fix', 'rejected', 'payment'])


class TestFOIAFunctional(TestCase):
    """Functional tests for FOIA"""
    fixtures = ['holidays.json', 'jurisdictions.json', 'agency_types.json', 'test_users.json',
                'test_profiles.json', 'test_foiarequests.json', 'test_foiacommunications.json',
                'test_agencies.json']

    # views
    def test_foia_list(self):
        """Test the foia-list view"""

        response = get_allowed(self.client, reverse('foia-list'))
        nose.tools.eq_(set(response.context['object_list']),
            set(FOIARequest.objects.get_viewable(AnonymousUser()).order_by('-date_submitted')[:12]))

    def test_foia_list_user(self):
        """Test the foia-list-user view"""

        for user_pk in [1, 2]:
            response = get_allowed(self.client,
                    reverse('foia-list-user', kwargs={'user_pk': user_pk}))
            user = User.objects.get(pk=user_pk)
            nose.tools.eq_(set(response.context['object_list']),
                           set(FOIARequest.objects.get_viewable(AnonymousUser()).filter(user=user)))
            nose.tools.ok_(all(foia.user == user for foia in response.context['object_list']))

    def test_foia_sorted_list(self):
        """Test sorting on foia-list view"""

        for field in ['title', 'date_submitted', 'status']:
            for order in ['asc', 'desc']:
                response = get_allowed(self.client, reverse('foia-list') +
                        '?sort=%s&order=%s' % (field, order))
                nose.tools.eq_([f.title for f in response.context['object_list']],
                               [f.title for f in sorted(response.context['object_list'],
                                                        key=attrgetter(field),
                                                        reverse=(order == 'desc'))])
    def test_foia_bad_sort(self):
        """Test sorting against a non-existant field"""
        response = get_allowed(self.client, reverse('foia-list') + '?sort=test')
        nose.tools.eq_(response.status_code, 200)

    def test_foia_detail(self):
        """Test the foia-detail view"""

        foia = FOIARequest.objects.get(pk=2)
        get_allowed(self.client,
                    reverse('foia-detail',
                        kwargs={'idx': foia.pk, 'slug': foia.slug,
                            'jurisdiction': foia.jurisdiction.slug,
                            'jidx': foia.jurisdiction.pk}))

    def test_feeds(self):
        """Test the RSS feed views"""

        get_allowed(self.client, reverse('foia-submitted-feed'))
        get_allowed(self.client, reverse('foia-done-feed'))

    def test_404_views(self):
        """Test views that should give a 404 error"""

        get_404(self.client, reverse('foia-detail', kwargs={'idx': 1, 'slug': 'test-c',
                                                       'jurisdiction': 'massachusetts',
                                                       'jidx': 1}))
        get_404(self.client, reverse('foia-detail', kwargs={'idx': 2, 'slug': 'test-c',
                                                       'jurisdiction': 'massachusetts',
                                                       'jidx': 1}))

    def test_unallowed_views(self):
        """Test private views while not logged in"""

        foia = FOIARequest.objects.get(pk=2)
        get_post_unallowed(self.client, reverse('foia-draft',
                                           kwargs={'jurisdiction': foia.jurisdiction.slug,
                                                   'jidx': foia.jurisdiction.pk,
                                                   'idx': foia.pk, 'slug': foia.slug}))

    def test_auth_views(self):
        """Test private views while logged in"""

        foia = FOIARequest.objects.get(pk=1)
        self.client.login(username='adam', password='abc')

        # get authenticated pages
        get_allowed(self.client, reverse('foia-create'))

        get_allowed(self.client, reverse('foia-draft',
            kwargs={'jurisdiction': foia.jurisdiction.slug,
                'jidx': foia.jurisdiction.pk,
                'idx': foia.pk, 'slug': foia.slug}))

        get_404(self.client, reverse('foia-draft',
                                kwargs={'jurisdiction': foia.jurisdiction.slug,
                                        'jidx': foia.jurisdiction.pk,
                                        'idx': foia.pk, 'slug': 'bad_slug'}))


    def test_foia_submit_views(self):
        """Test submitting a FOIA request"""

        foia = FOIARequest.objects.get(pk=1)
        agency = Agency.objects.get(pk=3)
        self.client.login(username='adam', password='abc')

        # test for submitting a foia request for enough credits
        # tests for the wizard

        foia_data = {'title': 'test a', 'request': 'updated request', 'submit': 'Submit',
                     'agency': agency.pk, 'combo-name': agency.name}

        kwargs = {'jurisdiction': foia.jurisdiction.slug,
                  'jidx': foia.jurisdiction.pk,
                  'idx': foia.pk, 'slug': foia.slug}
        draft = reverse('foia-draft', kwargs=kwargs)
        kwargs = {'jurisdiction': foia.jurisdiction.slug,
                  'jidx': foia.jurisdiction.pk,
                  'idx': foia.pk, 'slug': 'test-a'}
        detail = reverse('foia-detail', kwargs=kwargs)
        post_allowed(self.client, draft, foia_data, detail)

        foia = FOIARequest.objects.get(title='test a')
        nose.tools.ok_(foia.first_request().startswith('updated request'))
        nose.tools.eq_(foia.status, 'submitted')

    def test_foia_save_views(self):
        """Test saving a FOIA request"""

        foia = FOIARequest.objects.get(pk=6)
        self.client.login(username='bob', password='abc')

        foia_data = {'title': 'Test 6', 'request': 'saved request', 'submit': 'Save'}

        kwargs = {'jurisdiction': foia.jurisdiction.slug,
                  'jidx': foia.jurisdiction.pk,
                  'idx': foia.pk, 'slug': foia.slug}
        draft = reverse('foia-draft', kwargs=kwargs).replace('http://testserver', '')
        detail = reverse('foia-detail', kwargs=kwargs).replace('http://testserver', '')
        chain = [(url, 302) for url in (detail, draft)]
        response = self.client.post(draft, foia_data, follow=True)
        nose.tools.eq_(response.status_code, 200)
        nose.tools.eq_(response.redirect_chain, chain)

        foia = FOIARequest.objects.get(title='Test 6')
        nose.tools.ok_(foia.first_request().startswith('saved request'))
        nose.tools.eq_(foia.status, 'started')

    def test_action_views(self):
        """Test action views"""

        foia = FOIARequest.objects.get(pk=1)
        self.client.login(username='adam', password='abc')

        foia = FOIARequest.objects.get(pk=18)
        get_allowed(self.client, reverse('foia-pay',
            kwargs={'jurisdiction': foia.jurisdiction.slug,
                'jidx': foia.jurisdiction.pk,
                'idx': foia.pk, 'slug': foia.slug}))


class TestFOIAIntegration(TestCase):
    """Integration tests for FOIA"""
    # rewrite this with freezeray

    fixtures = ['holidays.json', 'jurisdictions.json', 'agency_types.json', 'test_users.json',
                'test_agencies.json', 'test_profiles.json', 'test_foiarequests.json',
                'test_foiacommunications.json']

    def setUp(self):
        """Set up tests"""
        # pylint: disable=bad-super-call

        mail.outbox = []

        import muckrock.foia.models.request

        # Replace real date and time with mock ones so we can control today's/now's value
        # Unfortunately need to monkey patch this a lot of places, and it gets rather ugly
        #http://tech.yunojuno.com/mocking-dates-with-django
        # pylint: disable=missing-docstring
        class MockDate(datetime.date):
            def __add__(self, other):
                d = super(MockDate, self).__add__(other)
                return MockDate(d.year, d.month, d.day)
            class MockDateType(type):
                "Used to ensure the FakeDate returns True to function calls."
                def __instancecheck__(self, instance):
                    return isinstance(instance, real_date)
            # this forces the FakeDate to return True to the isinstance date check
            __metaclass__ = MockDateType
        class MockDateTime(datetime.datetime):
            def date(self):
                return MockDate(self.year, self.month, self.day)

        self.orig_date = datetime.date
        self.orig_datetime = datetime.datetime
        datetime.date = MockDate
        datetime.datetime = MockDateTime
        muckrock.foia.models.request.date = datetime.date
        muckrock.foia.models.request.datetime = datetime.datetime
        def save(self, *args, **kwargs):
            if self.date_followup:
                self.date_followup = MockDateTime(self.date_followup.year,
                                                  self.date_followup.month,
                                                  self.date_followup.day)
            if self.date_done:
                self.date_done = MockDateTime(self.date_done.year,
                                              self.date_done.month,
                                              self.date_done.day)
            if 'comment' in kwargs:
                kwargs.pop('comment')
            super(FOIARequest, self).save(*args, **kwargs)
        self.FOIARequest_save = muckrock.foia.models.FOIARequest.save
        muckrock.foia.models.FOIARequest.save = save
        self.set_today(datetime.date(2010, 1, 1))

    def tearDown(self):
        """Tear down tests"""

        import muckrock.foia.models

        # restore the original date and datetime for other tests
        datetime.date = self.orig_date
        datetime.datetime = self.orig_datetime
        muckrock.foia.models.request.date = datetime.date
        muckrock.foia.models.request.datetime = datetime.datetime
        muckrock.foia.models.FOIARequest.save = self.FOIARequest_save

    def set_today(self, date):
        """Set what datetime thinks today is"""
        datetime.date.today = classmethod(lambda cls: cls(date.year, date.month, date.day))
        datetime.datetime.now = classmethod(lambda cls: cls(date.year, date.month, date.day))

    def test_request_lifecycle_no_email(self):
        """Test a request going through the full cycle as if we had to physically mail it"""
        # pylint: disable=too-many-statements
        # pylint: disable=protected-access

        user = User.objects.get(username='adam')
        agency = Agency.objects.get(pk=3)
        jurisdiction = Jurisdiction.objects.get(pk=1)
        cal = jurisdiction.get_calendar()

        self.set_today(datetime.date(2010, 2, 1))
        nose.tools.eq_(len(mail.outbox), 0)

        ## create and submit request
        foia = FOIARequest.objects.create(
            user=user, title='Test with no email', slug='test-with-no-email',
            status='submitted', jurisdiction=jurisdiction, agency=agency)
        comm = FOIACommunication.objects.create(
            foia=foia, from_who='Muckrock', to_who='Test Agency', date=datetime.datetime.now(),
            response=False, communication=u'Test communication')
        foia.submit()

        # check that a snail mail task was created
        nose.tools.ok_(
            SnailMailTask.objects.filter(
                communication=comm, category='n').exists())

        ## two days pass, then the admin mails in the request
        self.set_today(datetime.date.today() + datetime.timedelta(2))
        foia.status = 'processed'
        foia.update_dates()
        foia.save()

        # make sure dates were set correctly
        nose.tools.eq_(foia.date_submitted, datetime.date(2010, 2, 3))
        nose.tools.eq_(foia.date_due, cal.business_days_from(datetime.date.today(),
                                                             jurisdiction.get_days()))
        nose.tools.eq_(foia.date_followup.date(),
                       max(foia.date_due, foia.last_comm().date.date() +
                                          datetime.timedelta(foia._followup_days())))
        nose.tools.ok_(foia.days_until_due is None)
        # no more mail should have been sent
        nose.tools.eq_(len(mail.outbox), 0)

        old_date_due = foia.date_due

        ## after 5 days agency replies with a fix needed
        self.set_today(datetime.date.today() + datetime.timedelta(5))
        comm = FOIACommunication.objects.create(
            foia=foia, from_who='Test Agency', to_who='Muckrock', date=datetime.datetime.now(),
            response=True, communication='Test communication')
        foia.status = 'fix'
        foia.save()
        foia.update(comm.anchor())

        # make sure dates were set correctly
        nose.tools.eq_(foia.date_submitted, datetime.date(2010, 2, 3))
        nose.tools.ok_(foia.date_due is None)
        nose.tools.ok_(foia.date_followup is None)
        nose.tools.eq_(foia.days_until_due, cal.business_days_between(datetime.date(2010, 2, 8),
                                                                      old_date_due))

        old_days_until_due = foia.days_until_due

        ## after 10 days the user submits the fix and the admin submits it right away
        self.set_today(datetime.date.today() + datetime.timedelta(10))
        comm = FOIACommunication.objects.create(
            foia=foia, from_who='Muckrock', to_who='Test Agency', date=datetime.datetime.now(),
            response=False, communication='Test communication')
        foia.status = 'submitted'
        foia.save()
        foia.submit()

        # check that another snail mail task is created
        nose.tools.ok_(
            SnailMailTask.objects.filter(
                communication=comm, category='u').exists())

        foia.status = 'processed'

        foia.update_dates()
        foia.save()

        # make sure dates were set correctly
        nose.tools.eq_(foia.date_submitted, datetime.date(2010, 2, 3))
        nose.tools.eq_(foia.date_due, cal.business_days_from(datetime.date.today(),
                                                             old_days_until_due))
        nose.tools.eq_(foia.date_followup.date(),
                       max(foia.date_due, foia.last_comm().date.date() +
                                          datetime.timedelta(foia._followup_days())))
        nose.tools.ok_(foia.days_until_due is None)

        old_date_due = foia.date_due

        ## after 4 days agency replies with the documents
        self.set_today(datetime.date.today() + datetime.timedelta(4))
        comm = FOIACommunication.objects.create(
            foia=foia, from_who='Test Agency', to_who='Muckrock', date=datetime.datetime.now(),
            response=True, communication='Test communication')
        foia.status = 'done'
        foia.save()
        foia.update(comm.anchor())

        # make sure dates were set correctly
        nose.tools.eq_(foia.date_submitted, datetime.date(2010, 2, 3))
        nose.tools.eq_(foia.date_due, old_date_due)
        nose.tools.ok_(foia.date_followup is None)
        nose.tools.ok_(foia.days_until_due is None)


class TestFOIANotes(TestCase):
    """Allow editors to attach notes to a request."""
    def setUp(self):
        self.factory = RequestFactory()
        self.foia = FOIARequestFactory()
        self.creator = self.foia.user
        self.editor = UserFactory()
        self.viewer = UserFactory()
        self.foia.add_editor(self.editor)
        self.foia.add_viewer(self.viewer)
        self.note_text = u'Lorem ipsum dolor su ament.'
        self.note_data = {'action': 'add_note', 'note': self.note_text}

    def test_add_note(self):
        """User with edit permission should be able to create a note."""
        request = self.factory.post(self.foia.get_absolute_url(), self.note_data)
        request = mock_middleware(request)
        request.user = self.editor
        response = Detail.as_view()(
            request,
            jurisdiction=self.foia.jurisdiction.slug,
            jidx=self.foia.jurisdiction.id,
            slug=self.foia.slug,
            idx=self.foia.id
        )
        self.foia.refresh_from_db()
        nose.tools.eq_(response.status_code, 302)
        nose.tools.assert_true(self.foia.notes.count() > 0)

    def test_add_note_without_permission(self):
        """Normies and viewers cannot add notes."""
        request = self.factory.post(self.foia.get_absolute_url(), self.note_data)
        request = mock_middleware(request)
        request.user = self.viewer
        response = Detail.as_view()(
            request,
            jurisdiction=self.foia.jurisdiction.slug,
            jidx=self.foia.jurisdiction.id,
            slug=self.foia.slug,
            idx=self.foia.id
        )
        self.foia.refresh_from_db()
        nose.tools.eq_(response.status_code, 302)
        nose.tools.assert_true(self.foia.notes.count() == 0)


class TestRequestDetailView(TestCase):
    """Request detail views support a wide variety of interactions"""

    def setUp(self):
        self.foia = FOIARequestFactory()
        self.request_factory = RequestFactory()
        self.view = Detail.as_view()
        self.url = self.foia.get_absolute_url()

    def post_helper(self, data, user):
        """Returns post responses"""
        request = self.request_factory.post(self.url, data)
        request.user = user
        request = mock_middleware(request)
        return self.view(
            request,
            jurisdiction=self.foia.jurisdiction.slug,
            jidx=self.foia.jurisdiction.id,
            slug=self.foia.slug,
            idx=self.foia.id
        )

    def test_add_tags(self):
        """Posting a collection of tags to a request should update its tags."""
        tags = 'foo, bar'
        self.post_helper({'action': 'tags', 'tags': tags}, self.foia.user)
        self.foia.refresh_from_db()
        ok_('foo' in [tag.name for tag in self.foia.tags.all()])
        ok_('bar' in [tag.name for tag in self.foia.tags.all()])

    def test_add_projects(self):
        """Posting a collection of projects to a request should add it to those projects."""
        project = ProjectFactory()
        form = ProjectManagerForm({'projects': [project.pk]})
        ok_(form.is_valid())
        data = {'action': 'projects'}
        data.update(form.data)
        self.post_helper(data, self.foia.user)
        project.refresh_from_db()
        ok_(self.foia in project.requests.all())


class TestRequestPayment(TestCase):
    """Allow users to pay fees on a request"""
    def setUp(self):
        self.foia = FOIARequestFactory()

    def test_make_payment(self):
        """The request should accept payments for request fees."""
        user = self.foia.user
        amount = 100.0
        comm = self.foia.pay(user, amount)
        self.foia.refresh_from_db()
        eq_(self.foia.status, 'submitted',
            'The request should be set to processing.')
        eq_(self.foia.date_processing, datetime.date.today(),
            'The request should start tracking its days processing.')
        ok_(comm, 'The function should return a communication.')
        eq_(comm.delivered, 'mail', 'The communication should be mailed.')
        task = SnailMailTask.objects.filter(communication=comm).first()
        ok_(task, 'A snail mail task should be created.')
        eq_(task.user, user, 'The task should be attributed to the user.')
        eq_(task.amount, amount, 'The task should contain the amount of the request.')


class TestRequestSharing(TestCase):
    """Allow people to edit and view another user's request."""
    def setUp(self):
        self.foia = FOIARequestFactory()
        self.editor = UserFactory()
        self.creator = self.foia.user

    def test_add_editor(self):
        """Editors should be able to add editors to the request."""
        new_editor = self.editor
        self.foia.add_editor(new_editor)
        nose.tools.assert_true(self.foia.has_editor(new_editor))

    def test_remove_editor(self):
        """Editors should be able to remove editors from the request."""
        editor_to_remove = self.editor
        # first we add the editor, otherwise we would have nothing to remove!
        self.foia.add_editor(editor_to_remove)
        nose.tools.assert_true(self.foia.has_editor(editor_to_remove))
        # now we remove the editor we just added
        self.foia.remove_editor(editor_to_remove)
        nose.tools.assert_false(self.foia.has_editor(editor_to_remove))

    def test_editor_permission(self):
        """Editors should have the same abilities and permissions as creators."""
        new_editor = self.editor
        self.foia.add_editor(new_editor)
        nose.tools.ok_(self.foia.editable_by(new_editor))

    def test_add_viewer(self):
        """Editors should be able to add viewers to the request."""
        new_viewer = UserFactory()
        self.foia.add_viewer(new_viewer)
        nose.tools.ok_(self.foia.has_viewer(new_viewer))

    def test_remove_viewer(self):
        """Editors should be able to remove viewers from the request."""
        viewer_to_remove = UserFactory()
        # first we add the viewer, otherwise we would have nothing to remove!
        self.foia.add_viewer(viewer_to_remove)
        nose.tools.ok_(self.foia.has_viewer(viewer_to_remove))
        # now we remove the viewer we just added
        self.foia.remove_viewer(viewer_to_remove)
        nose.tools.assert_false(self.foia.has_viewer(viewer_to_remove))

    def test_viewer_permission(self):
        """Viewers should be able to see the request if it is embargoed."""
        embargoed_foia = FOIARequestFactory(embargo=True)
        viewer = UserFactory()
        normie = UserFactory()
        embargoed_foia.add_viewer(viewer)
        nose.tools.assert_true(embargoed_foia.viewable_by(viewer))
        nose.tools.assert_false(embargoed_foia.viewable_by(normie))

    def test_promote_viewer(self):
        """Editors should be able to promote viewers to editors."""
        embargoed_foia = FOIARequestFactory(embargo=True)
        viewer = UserFactory()
        embargoed_foia.add_viewer(viewer)
        nose.tools.assert_true(embargoed_foia.viewable_by(viewer))
        nose.tools.assert_false(embargoed_foia.editable_by(viewer))
        embargoed_foia.promote_viewer(viewer)
        nose.tools.assert_true(embargoed_foia.editable_by(viewer))

    def test_demote_editor(self):
        """Editors should be able to demote editors to viewers."""
        embargoed_foia = FOIARequestFactory(embargo=True)
        editor = UserFactory()
        embargoed_foia.add_editor(editor)
        nose.tools.assert_true(embargoed_foia.viewable_by(editor))
        nose.tools.assert_true(embargoed_foia.editable_by(editor))
        embargoed_foia.demote_editor(editor)
        nose.tools.assert_false(embargoed_foia.editable_by(editor))

    def test_access_key(self):
        """Editors should be able to generate a secure access key to view an embargoed request."""
        embargoed_foia = FOIARequestFactory(embargo=True)
        access_key = embargoed_foia.generate_access_key()
        nose.tools.assert_true(access_key == embargoed_foia.access_key,
            'The key in the URL should match the key saved to the request.')
        embargoed_foia.generate_access_key()
        nose.tools.assert_false(access_key == embargoed_foia.access_key,
            'After regenerating the link, the key should no longer match.')

    def test_do_not_grant_creator_access(self):
        """Creators should not be granted access as editors or viewers"""
        self.foia.add_editor(self.creator)
        nose.tools.assert_false(self.foia.has_editor(self.creator))
        self.foia.add_viewer(self.creator)
        nose.tools.assert_false(self.foia.has_viewer(self.creator))
        # but the creator should still be able to both view and edit!
        nose.tools.assert_true(self.foia.editable_by(self.creator))
        nose.tools.assert_true(self.foia.viewable_by(self.creator))


class TestRequestSharingViews(TestCase):
    """Tests access and implementation of view methods for sharing requests."""
    def setUp(self):
        self.factory = RequestFactory()
        self.foia = FOIARequestFactory()
        self.creator = self.foia.user
        self.editor = UserFactory()
        self.viewer = UserFactory()
        self.staff = UserFactory(is_staff=True)
        self.normie = UserFactory()
        self.foia.add_editor(self.editor)
        self.foia.add_viewer(self.viewer)
        self.foia.save()

    def reset_access_key(self):
        """Simple helper to reset access key betweeen tests"""
        self.foia.access_key = None
        nose.tools.assert_false(self.foia.access_key)

    def test_access_key_allowed(self):
        """
        A POST request for a private share link should generate and return an access key.
        Editors and staff should be allowed to do this.
        """
        self.reset_access_key()
        data = {'action': 'generate_key'}
        request = self.factory.post(self.foia.get_absolute_url(), data)
        request = mock_middleware(request)
        # editors should be able to generate the key
        request.user = self.editor
        response = Detail.as_view()(
            request,
            jurisdiction=self.foia.jurisdiction.slug,
            jidx=self.foia.jurisdiction.id,
            slug=self.foia.slug,
            idx=self.foia.id
        )
        self.foia.refresh_from_db()
        nose.tools.eq_(response.status_code, 302)
        nose.tools.assert_true(self.foia.access_key)
        # staff should be able to generate the key
        self.reset_access_key()
        request.user = self.staff
        response = Detail.as_view()(
            request,
            jurisdiction=self.foia.jurisdiction.slug,
            jidx=self.foia.jurisdiction.id,
            slug=self.foia.slug,
            idx=self.foia.id
        )
        self.foia.refresh_from_db()
        nose.tools.eq_(response.status_code, 302)
        nose.tools.assert_true(self.foia.access_key)

    def test_access_key_not_allowed(self):
        """Visitors and normies should not be allowed to generate an access key."""
        self.reset_access_key()
        data = {'action': 'generate_key'}
        request = self.factory.post(self.foia.get_absolute_url(), data)
        request = mock_middleware(request)
        # viewers should not be able to generate the key
        request.user = self.viewer
        response = Detail.as_view()(
            request,
            jurisdiction=self.foia.jurisdiction.slug,
            jidx=self.foia.jurisdiction.id,
            slug=self.foia.slug,
            idx=self.foia.id
        )
        self.foia.refresh_from_db()
        nose.tools.eq_(response.status_code, 302)
        nose.tools.assert_false(self.foia.access_key)
        # normies should not be able to generate the key
        self.reset_access_key()
        request.user = self.normie
        response = Detail.as_view()(
            request,
            jurisdiction=self.foia.jurisdiction.slug,
            jidx=self.foia.jurisdiction.id,
            slug=self.foia.slug,
            idx=self.foia.id
        )
        self.foia.refresh_from_db()
        nose.tools.eq_(response.status_code, 302)
        nose.tools.assert_false(self.foia.access_key)

    def test_grant_edit_access(self):
        """Editors should be able to add editors."""
        user1 = UserFactory()
        user2 = UserFactory()
        edit_data = {
            'action': 'grant_access',
            'users': [user1.pk, user2.pk],
            'access': 'edit'
        }
        edit_request = self.factory.post(self.foia.get_absolute_url(), edit_data)
        edit_request = mock_middleware(edit_request)
        edit_request.user = self.editor
        edit_response = Detail.as_view()(
            edit_request,
            jurisdiction=self.foia.jurisdiction.slug,
            jidx=self.foia.jurisdiction.id,
            slug=self.foia.slug,
            idx=self.foia.id
        )
        nose.tools.eq_(edit_response.status_code, 302)
        nose.tools.assert_true(self.foia.has_editor(user1) and self.foia.has_editor(user2))

    def test_grant_view_access(self):
        """Editors should be able to add viewers."""
        user1 = UserFactory()
        user2 = UserFactory()
        view_data = {
            'action': 'grant_access',
            'users': [user1.pk, user2.pk],
            'access': 'view'
        }
        view_request = self.factory.post(self.foia.get_absolute_url(), view_data)
        view_request = mock_middleware(view_request)
        view_request.user = self.editor
        view_response = Detail.as_view()(
            view_request,
            jurisdiction=self.foia.jurisdiction.slug,
            jidx=self.foia.jurisdiction.id,
            slug=self.foia.slug,
            idx=self.foia.id
        )
        nose.tools.eq_(view_response.status_code, 302)
        nose.tools.assert_true(self.foia.has_viewer(user1) and self.foia.has_viewer(user2))

    def test_demote_editor(self):
        """Editors should be able to demote editors to viewers."""
        user = UserFactory()
        self.foia.add_editor(user)
        nose.tools.assert_true(self.foia.has_editor(user))
        data = {
            'action': 'demote',
            'user': user.pk
        }
        request = self.factory.post(self.foia.get_absolute_url(), data)
        request = mock_middleware(request)
        request.user = self.editor
        response = Detail.as_view()(
            request,
            jurisdiction=self.foia.jurisdiction.slug,
            jidx=self.foia.jurisdiction.id,
            slug=self.foia.slug,
            idx=self.foia.id
        )
        nose.tools.eq_(response.status_code, 302)
        nose.tools.assert_false(self.foia.has_editor(user))
        nose.tools.assert_true(self.foia.has_viewer(user))

    def test_promote_viewer(self):
        """Editors should be able to promote viewers to editors."""
        user = UserFactory()
        self.foia.add_viewer(user)
        nose.tools.assert_true(self.foia.has_viewer(user))
        data = {
            'action': 'promote',
            'user': user.pk
        }
        request = self.factory.post(self.foia.get_absolute_url(), data)
        request = mock_middleware(request)
        request.user = self.editor
        response = Detail.as_view()(
            request,
            jurisdiction=self.foia.jurisdiction.slug,
            jidx=self.foia.jurisdiction.id,
            slug=self.foia.slug,
            idx=self.foia.id
        )
        nose.tools.eq_(response.status_code, 302)
        nose.tools.assert_false(self.foia.has_viewer(user))
        nose.tools.assert_true(self.foia.has_editor(user))

    def test_revoke_edit_access(self):
        """Editors should be able to revoke access from an editor."""
        an_editor = UserFactory()
        self.foia.add_editor(an_editor)
        data = {
            'action': 'revoke_access',
            'user': an_editor.pk
        }
        request = self.factory.post(self.foia.get_absolute_url(), data)
        request = mock_middleware(request)
        request.user = self.editor
        response = Detail.as_view()(
            request,
            jurisdiction=self.foia.jurisdiction.slug,
            jidx=self.foia.jurisdiction.id,
            slug=self.foia.slug,
            idx=self.foia.id
        )
        nose.tools.eq_(response.status_code, 302)
        nose.tools.assert_false(self.foia.has_editor(an_editor))

    def test_revoke_view_access(self):
        """Editors should be able to revoke access from a viewer."""
        a_viewer = UserFactory()
        self.foia.add_viewer(a_viewer)
        data = {
            'action': 'revoke_access',
            'user': a_viewer.pk
        }
        request = self.factory.post(self.foia.get_absolute_url(), data)
        request = mock_middleware(request)
        request.user = self.editor
        response = Detail.as_view()(
            request,
            jurisdiction=self.foia.jurisdiction.slug,
            jidx=self.foia.jurisdiction.id,
            slug=self.foia.slug,
            idx=self.foia.id
        )
        nose.tools.eq_(response.status_code, 302)
        nose.tools.assert_false(self.foia.has_viewer(a_viewer))


class TestRequestFilesView(TestCase):
    """Files should render in a paginated list on a separate page."""
    def setUp(self):
        self.file = FOIAFileFactory()
        self.foia = self.file.foia
        self.kwargs = {
            'idx': self.foia.pk,
            'slug': self.foia.slug,
            'jidx': self.foia.jurisdiction.pk,
            'jurisdiction': self.foia.jurisdiction.slug
        }
        self.url = reverse('foia-files', kwargs=self.kwargs)
        self.view = FOIAFileListView.as_view()
        self.factory = RequestFactory()

    def test_get_ok(self):
        """The view should return 200 if the foia is viewable to the user."""
        request = self.factory.get(self.url)
        request.user = self.foia.user
        request = mock_middleware(request)
        ok_(self.foia.viewable_by(request.user), 'The user should be able to view the request')
        response = self.view(
            request,
            jurisdiction=self.foia.jurisdiction.slug,
            jidx=self.foia.jurisdiction.id,
            slug=self.foia.slug,
            idx=self.foia.id
        )
        eq_(response.status_code, 200, 'The view should return 200.')

    @raises(Http404)
    def test_get_404(self):
        """The view should return 404 is the foia is not visible to the user."""
        self.foia.embargo = True
        self.foia.save()
        user = UserFactory()
        ok_(not self.foia.viewable_by(user))
        request = self.factory.get(self.url)
        request.user = user
        request = mock_middleware(request)
        self.view(
            request,
            jurisdiction=self.foia.jurisdiction.slug,
            jidx=self.foia.jurisdiction.id,
            slug=self.foia.slug,
            idx=self.foia.id
        )

class TestMakeUser(TestCase):
    """The request composer should provide miniregistration functionality."""
    def setUp(self):
        self.request = mock_middleware(Mock())
        self.data = {
            'full_name': 'Mick Jagger',
            'email': 'mick@hero.in'
        }

    def test_make_user(self):
        """Should create the user, log them in, and return the user."""
        user = _make_user(self.request, self.data)
        ok_(user)
