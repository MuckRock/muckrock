"""
Tests using nose for the FOIA application
"""

from django.contrib.auth.models import AnonymousUser
from django.core.urlresolvers import reverse
from django.core import mail
from django.test import TestCase

from actstream.actions import follow
import datetime
from mock import Mock
import nose.tools
from nose.tools import ok_, eq_, assert_false
from operator import attrgetter
import re
from freezegun import freeze_time

from muckrock.factories import (
        UserFactory,
        FOIARequestFactory,
        FOIACommunicationFactory,
        ProjectFactory,
        AgencyFactory,
        AgencyUserFactory,
        FederalJurisdictionFactory,
        AppealAgencyFactory,
        )
from muckrock.accounts.models import AgencyUser
from muckrock.foia.models import FOIARequest, FOIACommunication
from muckrock.foia.views import Detail
from muckrock.foia.views.composers import _make_user
from muckrock.jurisdiction.factories import ExampleAppealFactory
from muckrock.jurisdiction.models import Appeal
from muckrock.project.forms import ProjectManagerForm
from muckrock.task.models import SnailMailTask
from muckrock.tests import get_allowed, post_allowed, get_post_unallowed, get_404
from muckrock.test_utils import mock_middleware, http_post_response
from muckrock.utils import new_action

# allow methods that could be functions and too many public methods in tests
# pylint: disable=no-self-use
# pylint: disable=too-many-public-methods
# pylint: disable=too-many-lines
# pylint: disable=invalid-name
# pylint: disable=bad-mcs-method-argument

class TestFOIARequestUnit(TestCase):
    """Unit tests for FOIARequests"""

    # models
    def test_foia_model_unicode(self):
        """Test FOIA Request model's __unicode__ method"""
        foia = FOIARequestFactory(title='Test 1')
        nose.tools.eq_(unicode(foia), 'Test 1')

    def test_foia_model_url(self):
        """Test FOIA Request model's get_absolute_url method"""
        foia = FOIARequestFactory(
                slug='test-1', jurisdiction__slug='massachusetts')
        nose.tools.eq_(foia.get_absolute_url(),
            reverse('foia-detail', kwargs={'idx': foia.pk, 'slug': 'test-1',
                                           'jurisdiction': 'massachusetts',
                                           'jidx': foia.jurisdiction.pk}))

    def test_foia_model_editable(self):
        """Test FOIA Request model's is_editable method"""
        foia1 = FOIARequestFactory(status='started')
        foia2 = FOIARequestFactory(status='done')
        nose.tools.assert_true(foia1.is_editable())
        nose.tools.assert_false(foia2.is_editable())

    def test_foia_viewable(self):
        """Test all the viewable and embargo functions"""

        user1 = UserFactory()
        user2 = UserFactory()

        foia0 = FOIARequestFactory(status='started', user=user1)
        foia1 = FOIARequestFactory(
                status='done', embargo=False, user=user1,
                date_embargo=datetime.date.today() + datetime.timedelta(10))
        foia2 = FOIARequestFactory(
                status='done', embargo=True, user=user1,
                date_embargo=datetime.date.today())
        foia3 = FOIARequestFactory(
                status='done', embargo=False, user=user1,
                date_embargo=datetime.date.today() - datetime.timedelta(1))
        foia4 = FOIARequestFactory(
                status='done', embargo=False, user=user1)
        FOIARequestFactory(
                status='submitted', embargo=True, user=user1,
                date_embargo=datetime.date.today() - datetime.timedelta(10))

        # check manager get_viewable against view permission
        viewable_foias = FOIARequest.objects.get_viewable(user1)
        for foia in FOIARequest.objects.all():
            if foia in viewable_foias:
                nose.tools.assert_true(user1.has_perm('foia.view_foiarequest', foia))
            else:
                nose.tools.assert_false(user1.has_perm('foia.view_foiarequest', foia))

        viewable_foias = FOIARequest.objects.get_viewable(user2)
        for foia in FOIARequest.objects.all():
            if foia in viewable_foias:
                nose.tools.assert_true(user2.has_perm('foia.view_foiarequest', foia))
            else:
                nose.tools.assert_false(user2.has_perm('foia.view_foiarequest', foia))

        viewable_foias = FOIARequest.objects.get_public()
        for foia in FOIARequest.objects.all():
            if foia in viewable_foias:
                nose.tools.assert_true(AnonymousUser().has_perm('foia.view_foiarequest', foia))
            else:
                nose.tools.assert_false(AnonymousUser().has_perm('foia.view_foiarequest', foia))

        nose.tools.assert_true(user1.has_perm('foia.view_foiarequest', foia0))
        nose.tools.assert_true(user1.has_perm('foia.view_foiarequest', foia1))
        nose.tools.assert_true(user1.has_perm('foia.view_foiarequest', foia2))
        nose.tools.assert_true(user1.has_perm('foia.view_foiarequest', foia3))
        nose.tools.assert_true(user1.has_perm('foia.view_foiarequest', foia4))

        nose.tools.assert_false(user2.has_perm('foia.view_foiarequest', foia0))
        nose.tools.assert_true(user2.has_perm('foia.view_foiarequest', foia1))
        nose.tools.assert_false(user2.has_perm('foia.view_foiarequest', foia2))
        nose.tools.assert_true(user2.has_perm('foia.view_foiarequest', foia3))
        nose.tools.assert_true(user2.has_perm('foia.view_foiarequest', foia4))

        nose.tools.assert_false(AnonymousUser().has_perm('foia.view_foiarequest', foia0))
        nose.tools.assert_true(AnonymousUser().has_perm('foia.view_foiarequest', foia1))
        nose.tools.assert_false(AnonymousUser().has_perm('foia.view_foiarequest', foia2))
        nose.tools.assert_true(AnonymousUser().has_perm('foia.view_foiarequest', foia3))
        nose.tools.assert_true(AnonymousUser().has_perm('foia.view_foiarequest', foia4))

    def test_foia_set_mail_id(self):
        """Test the set_mail_id function"""
        foia = FOIARequestFactory()
        foia.set_mail_id()
        mail_id = foia.mail_id
        nose.tools.ok_(re.match(r'\d{1,4}-\d{8}', mail_id))

        foia.set_mail_id()
        nose.tools.eq_(mail_id, foia.mail_id)

    def test_foia_followup(self):
        """Make sure the follow up date is set correctly"""
        # pylint: disable=protected-access
        mail.outbox = []
        UserFactory(username='MuckrockStaff')
        foia = FOIARequestFactory(status='processed',
                contacts=(AgencyUserFactory(email='test@agency.gov'),))

        foia.followup()
        nose.tools.assert_in('I can expect', mail.outbox[-1].body)
        nose.tools.eq_(
                foia.date_followup,
                datetime.date.today() + datetime.timedelta(foia._followup_days()))

        nose.tools.eq_(foia._followup_days(), 30)

        num_days = 365
        foia.date_estimate = datetime.date.today() + datetime.timedelta(num_days)
        foia.followup()
        nose.tools.assert_in('I am still', mail.outbox[-1].body)
        nose.tools.eq_(foia._followup_days(), num_days)

        foia.date_estimate = datetime.date.today()
        foia.followup()
        nose.tools.assert_in('check on the status', mail.outbox[-1].body)
        nose.tools.eq_(foia._followup_days(), 30)

    def test_foia_followup_estimated(self):
        """If request has an estimated date, returns number of days until the estimated date"""
        # pylint: disable=protected-access
        num_days = 365
        foia = FOIARequestFactory(status='processed')
        foia.date_estimate = datetime.date.today() + datetime.timedelta(num_days)
        nose.tools.eq_(foia._followup_days(), num_days)

     # manager
    def test_manager_get_submitted(self):
        """Test the FOIA Manager's get_submitted method"""

        for status in ('started', 'ack', 'done'):
            FOIARequestFactory(status=status)

        submitted_foias = FOIARequest.objects.get_submitted()
        for foia in FOIARequest.objects.all():
            if foia in submitted_foias:
                nose.tools.ok_(foia.status != 'started')
            else:
                nose.tools.ok_(foia.status == 'started')

    def test_manager_get_done(self):
        """Test the FOIA Manager's get_done method"""
        for status in ('started', 'submitted', 'processed'):
            FOIARequestFactory(status=status)
        FOIARequestFactory(status='done', date_done=datetime.date.today())

        done_foias = FOIARequest.objects.get_done()
        for foia in FOIARequest.objects.all():
            if foia in done_foias:
                nose.tools.eq_(foia.status, 'done')
            else:
                nose.tools.assert_in(foia.status,
                        ['started', 'submitted', 'processed',
                            'fix', 'rejected', 'payment'])


class TestFOIAFunctional(TestCase):
    """Functional tests for FOIA"""

    # views
    def test_foia_list(self):
        """Test the foia-list view"""
        response = get_allowed(self.client, reverse('foia-list'))
        nose.tools.eq_(
                set(response.context['object_list']),
                set(FOIARequest.objects
                    .get_viewable(AnonymousUser())
                    .order_by('-date_submitted')[:12]))

    def test_foia_list_user(self):
        """Test the foia-list-user view"""
        users = UserFactory.create_batch(2)
        FOIARequestFactory.create_batch(3, user=users[0])
        FOIARequestFactory.create_batch(3, user=users[1])
        for user in users:
            response = get_allowed(self.client,
                    reverse('foia-list-user', kwargs={'user_pk': user.pk}))
            nose.tools.eq_(
                    set(response.context['object_list']),
                    set(FOIARequest.objects
                        .get_viewable(AnonymousUser())
                        .filter(user=user)))
            nose.tools.ok_(all(foia.user == user
                for foia in response.context['object_list']))

    def test_foia_sorted_list(self):
        """Test sorting on foia-list view"""
        for days_ago, status in (
                (1, 'submitted'),
                (5, 'fix'),
                (25, 'rejected'),
                (300, 'submitted')):
            FOIARequestFactory(
                    date_submitted=datetime.date.today() -
                        datetime.timedelta(days_ago),
                    status=status)

        for field in ['title', 'date_submitted', 'status']:
            for order in ['asc', 'desc']:
                response = get_allowed(self.client,
                        reverse('foia-list') +
                        '?sort=%s&order=%s' % (field, order))
                nose.tools.eq_(
                        [f.title for f in response.context['object_list']],
                        [f.title for f in
                            sorted(response.context['object_list'],
                                key=attrgetter(field),
                                reverse=(order == 'desc'))])

    def test_foia_bad_sort(self):
        """Test sorting against a non-existant field"""
        response = get_allowed(self.client, reverse('foia-list') + '?sort=test')
        nose.tools.eq_(response.status_code, 200)

    def test_foia_detail(self):
        """Test the foia-detail view"""
        foia = FOIARequestFactory()
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
        get_404(self.client,
                reverse('foia-detail',
                    kwargs={'idx': 1, 'slug': 'test-c',
                        'jurisdiction': 'massachusetts',
                        'jidx': 1}))
        get_404(self.client,
                reverse('foia-detail',
                    kwargs={'idx': 2, 'slug': 'test-c',
                        'jurisdiction': 'massachusetts',
                        'jidx': 1}))

    def test_unallowed_views(self):
        """Test private views while not logged in"""
        foia = FOIARequestFactory()
        get_post_unallowed(self.client,
                reverse('foia-draft',
                    kwargs={
                        'jurisdiction': foia.jurisdiction.slug,
                        'jidx': foia.jurisdiction.pk,
                        'idx': foia.pk,
                        'slug': foia.slug}))

    def test_auth_views(self):
        """Test private views while logged in"""

        foia = FOIARequestFactory(
                status='started', user__username='adam', user__password='abc')
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

        foia = FOIARequestFactory(
                status='started', user__username='adam', user__password='abc')
        FOIACommunicationFactory(foia=foia)
        agency = AgencyFactory()
        self.client.login(username='adam', password='abc')

        # test for submitting a foia request for enough credits

        foia_data = {
                'title': 'test a',
                'request': 'updated request',
                'submit': 'Submit',
                'agency': agency.pk,
                'combo-name': agency.name}

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

        foia = FOIARequestFactory(
                status='started', user__username='bob', user__password='abc')
        FOIACommunicationFactory(foia=foia)
        self.client.login(username='bob', password='abc')

        foia_data = {
                'title': foia.title,
                'request': 'saved request',
                'submit': 'Save'}

        kwargs = {'jurisdiction': foia.jurisdiction.slug,
                  'jidx': foia.jurisdiction.pk,
                  'idx': foia.pk, 'slug': foia.slug}
        draft = (reverse('foia-draft', kwargs=kwargs)
                .replace('http://testserver', ''))
        detail = (reverse('foia-detail', kwargs=kwargs)
                .replace('http://testserver', ''))
        chain = [(url, 302) for url in (detail, draft)]
        response = self.client.post(draft, foia_data, follow=True)
        nose.tools.eq_(response.status_code, 200)
        nose.tools.eq_(response.redirect_chain, chain)

        foia = FOIARequest.objects.get(title=foia.title)
        nose.tools.ok_(foia.first_request().startswith('saved request'))
        nose.tools.eq_(foia.status, 'started')

    def test_action_views(self):
        """Test action views"""

        foia = FOIARequestFactory()
        self.client.login(username='adam', password='abc')

        foia = FOIARequestFactory(status='payment')
        get_allowed(self.client, reverse('foia-pay',
            kwargs={'jurisdiction': foia.jurisdiction.slug,
                'jidx': foia.jurisdiction.pk,
                'idx': foia.pk, 'slug': foia.slug}))


class TestFOIAIntegration(TestCase):
    """Integration tests for FOIA"""

    def test_request_lifecycle_no_email(self):
        """Test a request going through the full cycle as if we had to physically mail it"""
        # pylint: disable=too-many-statements
        # pylint: disable=protected-access

        mail.outbox = []

        user = UserFactory()
        agency = AgencyFactory()
        jurisdiction = FederalJurisdictionFactory()
        cal = jurisdiction.get_calendar()

        with freeze_time('2010-02-01'):
            nose.tools.eq_(len(mail.outbox), 0)

            ## create and submit request
            foia = FOIARequest.objects.create(
                user=user, title='Test with no email', slug='test-with-no-email',
                status='submitted', jurisdiction=jurisdiction, agency=agency)
            comm = FOIACommunication.objects.create(
                foia=foia, from_who='Muckrock', date=datetime.datetime.now(),
                response=False, communication=u'Test communication')
            foia.submit()

            # check that a snail mail task was created
            nose.tools.ok_(
                SnailMailTask.objects.filter(
                    communication=comm, category='n').exists())

        ## two days pass, then the admin mails in the request
        with freeze_time('2010-02-03'):
            foia.status = 'processed'
            foia.update_dates()
            foia.save()

            # make sure dates were set correctly
            nose.tools.eq_(foia.date_submitted, datetime.date(2010, 2, 3))
            nose.tools.eq_(
                    foia.date_due,
                    cal.business_days_from(
                        datetime.date.today(),
                        jurisdiction.get_days()))
            nose.tools.eq_(
                    foia.date_followup,
                    max(
                        foia.date_due,
                        foia.last_comm().date.date() +
                            datetime.timedelta(foia._followup_days())))
            nose.tools.assert_is_none(foia.days_until_due)
            # no more mail should have been sent
            nose.tools.eq_(len(mail.outbox), 0)

            old_date_due = foia.date_due

        ## after 5 days agency replies with a fix needed
        with freeze_time('2010-02-08'):
            comm = FOIACommunication.objects.create(
                foia=foia, from_who='Test Agency', date=datetime.datetime.now(),
                response=True, communication='Test communication')
            foia.status = 'fix'
            foia.save()
            foia.update(comm.anchor())

            # make sure dates were set correctly
            nose.tools.eq_(foia.date_submitted, datetime.date(2010, 2, 3))
            nose.tools.assert_is_none(foia.date_due)
            nose.tools.assert_is_none(foia.date_followup)
            nose.tools.eq_(
                    foia.days_until_due,
                    cal.business_days_between(
                        datetime.date(2010, 2, 8),
                        old_date_due))

            old_days_until_due = foia.days_until_due

        ## after 10 days the user submits the fix and the admin submits it right away
        with freeze_time('2010-02-18'):
            comm = FOIACommunication.objects.create(
                foia=foia, from_who='Muckrock', date=datetime.datetime.now(),
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
            nose.tools.eq_(
                    foia.date_due,
                    cal.business_days_from(
                        datetime.date.today(),
                        old_days_until_due))
            nose.tools.eq_(
                    foia.date_followup,
                    max(
                        foia.date_due,
                        foia.last_comm().date.date() +
                            datetime.timedelta(foia._followup_days())))
            nose.tools.assert_is_none(foia.days_until_due)

            old_date_due = foia.date_due

        ## after 4 days agency replies with the documents
        with freeze_time('2010-02-22'):
            comm = FOIACommunication.objects.create(
                foia=foia, from_who='Test Agency', date=datetime.datetime.now(),
                response=True, communication='Test communication')
            foia.status = 'done'
            foia.save()
            foia.update(comm.anchor())

            # make sure dates were set correctly
            nose.tools.eq_(foia.date_submitted, datetime.date(2010, 2, 3))
            nose.tools.eq_(foia.date_due, old_date_due)
            nose.tools.assert_is_none(foia.date_followup)
            nose.tools.assert_is_none(foia.days_until_due)


class TestFOIARequestAppeal(TestCase):
    """A request should be able to send an appeal to the agency that receives them."""
    def setUp(self):
        self.appeal_agency = AppealAgencyFactory()
        self.agency = AgencyFactory(status='approved', appeal_agency=self.appeal_agency)
        self.foia = FOIARequestFactory(agency=self.agency, status='rejected')

    def test_appeal(self):
        """Sending an appeal to the agency should require the message for the appeal,
        which is then turned into a communication to the correct agency. In this case,
        the correct agency is the same one that received the message."""
        ok_(self.foia.user.has_perm('foia.appeal_foiarequest', self.foia),
            'The request should be appealable.')
        ok_(self.agency and self.agency.status == 'approved',
            'The agency should be approved.')
        # XXX check this in a different way
        #ok_(self.appeal_agency.email and self.appeal_agency.can_email_appeals,
        #    'The appeal agency should accept email.')
        # Create the appeal message and submit it
        appeal_message = 'Lorem ipsum'
        appeal_comm = self.foia.appeal(appeal_message)
        # Check that everything happened like we expected
        self.foia.refresh_from_db()
        appeal_comm.refresh_from_db()
        # XXX
        #eq_(self.foia.email, self.appeal_agency.email,
        #    'The FOIA primary email should be set to the appeal agency\'s email.')
        eq_(self.foia.status, 'appealing',
            'The status of the request should be updated. Actually: %s' % self.foia.status)
        eq_(appeal_comm.communication, appeal_message,
            'The appeal message parameter should be used as the body of the communication.')
        # XXX
        #eq_(appeal_comm.from_who, self.foia.user.get_full_name(),
        #    'The appeal should be addressed from the request owner.')
        #eq_(appeal_comm.to_who, self.agency.name,
        #    'The appeal should be addressed to the agency.')
        eq_(appeal_comm.delivered, 'email',
            'The appeal should be marked as delivered via email, not %s.' % appeal_comm.delivered)

    def test_mailed_appeal(self):
        """Sending an appeal to an agency via mail should set the request to 'submitted',
        create a snail mail task with the 'a' category, and set the appeal communication
        delivery method to 'mail'."""
        # Make the appeal agency unreceptive to emails
        appeal_user = self.appeal_agency.users.first()
        appeal_user.email = ''
        appeal_user.save()
        # Create the appeal message and submit it
        appeal_message = 'Lorem ipsum'
        appeal_comm = self.foia.appeal(appeal_message)
        # Check that everything happened like we expected
        self.foia.refresh_from_db()
        appeal_comm.refresh_from_db()
        eq_(self.foia.status, 'submitted',
            'The status of the request should be updated. Actually: %s' % self.foia.status)
        eq_(appeal_comm.communication, appeal_message,
            'The appeal message parameter should be used as the body of the communication.')
        eq_(appeal_comm.from_who, self.foia.user.get_full_name(),
            'The appeal should be addressed from the request owner.')
        # XXX
        #eq_(appeal_comm.to_who, self.agency.name)
            #'The appeal should be addressed to the agency.')
        eq_(
                list(AgencyUser.objects.filter(
                    pk__in=appeal_comm.to_users.values_list('pk', flat=True))),
                list(self.foia.get_contacts('appeal', 'to')))
        eq_(appeal_comm.delivered, 'mail',
            'The appeal should be marked as delivered via mail, not %s.' % appeal_comm.delivered)
        task = SnailMailTask.objects.get(communication=appeal_comm)
        ok_(task, 'A snail mail task should be created.')
        eq_(task.category, 'a', 'The task should be in the appeal category.')


class TestRequestDetailView(TestCase):
    """Request detail views support a wide variety of interactions"""
    def setUp(self):
        agency = AgencyFactory(appeal_agency=AppealAgencyFactory())
        self.foia = FOIARequestFactory(agency=agency)
        self.view = Detail.as_view()
        self.url = self.foia.get_absolute_url()
        self.kwargs = {
            'jurisdiction': self.foia.jurisdiction.slug,
            'jidx': self.foia.jurisdiction.id,
            'slug': self.foia.slug,
            'idx': self.foia.id
        }

    def test_add_tags(self):
        """Posting a collection of tags to a request should update its tags."""
        data = {'action': 'tags', 'tags': 'foo, bar'}
        http_post_response(self.url, self.view, data, self.foia.user, **self.kwargs)
        self.foia.refresh_from_db()
        nose.tools.ok_('foo' in [tag.name for tag in self.foia.tags.all()])
        nose.tools.ok_('bar' in [tag.name for tag in self.foia.tags.all()])

    def test_add_projects(self):
        """Posting a collection of projects to a request should add it to those projects."""
        project = ProjectFactory()
        form = ProjectManagerForm({'projects': [project.pk]})
        nose.tools.ok_(form.is_valid())
        data = {'action': 'projects'}
        data.update(form.data)
        http_post_response(self.url, self.view, data, self.foia.user, **self.kwargs)
        project.refresh_from_db()
        nose.tools.ok_(self.foia in project.requests.all())

    def test_appeal(self):
        """Appealing a request should send a new communication,
        record the details of the appeal, and update the status of the request."""
        comm_count = self.foia.communications.count()
        data = {'action': 'appeal', 'text': 'Lorem ipsum'}
        http_post_response(self.url, self.view, data, self.foia.user, **self.kwargs)
        self.foia.refresh_from_db()
        eq_(self.foia.status, 'appealing')
        eq_(self.foia.communications.count(), comm_count + 1)
        eq_(self.foia.last_comm().communication, data['text'],
            'The appeal should use the language provided by the user.')
        appeal = Appeal.objects.last()
        ok_(appeal, 'An Appeal object should be created.')
        eq_(self.foia.last_comm(), appeal.communication,
            'The appeal should reference the communication that was created.')

    def test_appeal_example(self):
        """If an example appeal is used to base the appeal off of,
        then the examples should be recorded to the appeal object as well."""
        example_appeal = ExampleAppealFactory()
        data = {'action': 'appeal', 'text': 'Lorem ipsum', 'base_language': example_appeal.pk}
        http_post_response(self.url, self.view, data, self.foia.user, **self.kwargs)
        self.foia.refresh_from_db()
        appeal = Appeal.objects.last()
        ok_(appeal.base_language, 'The appeal should record its base language.')
        ok_(appeal.base_language.count(), 1)

    def test_unauthorized_appeal(self):
        """Appealing a request without permission should not do anything."""
        unauth_user = UserFactory()
        comm_count = self.foia.communications.count()
        previous_status = self.foia.status
        data = {'action': 'appeal', 'text': 'Lorem ipsum'}
        http_post_response(self.url, self.view, data, unauth_user, **self.kwargs)
        self.foia.refresh_from_db()
        eq_(self.foia.status, previous_status,
            'The status of the request should not be changed.')
        eq_(self.foia.communications.count(), comm_count,
            'No communication should be added to the request.')

    def test_missing_appeal(self):
        """An appeal that is missing its language should not do anything."""
        comm_count = self.foia.communications.count()
        previous_status = self.foia.status
        data = {'action': 'appeal', 'text': ''}
        http_post_response(self.url, self.view, data, self.foia.user, **self.kwargs)
        self.foia.refresh_from_db()
        eq_(self.foia.status, previous_status,
            'The status of the request should not be changed.')
        eq_(self.foia.communications.count(), comm_count,
            'No communication should be added to the request.')

    def test_unappealable_request(self):
        """An appeal on a request that cannot be appealed should not do anything."""
        self.foia.status = 'submitted'
        self.foia.save()
        assert_false(self.foia.user.has_perm('foia.appeal_foiarequest', self.foia))
        comm_count = self.foia.communications.count()
        previous_status = self.foia.status
        data = {'action': 'appeal', 'text': 'Lorem ipsum'}
        http_post_response(self.url, self.view, data, self.foia.user, **self.kwargs)
        self.foia.refresh_from_db()
        eq_(self.foia.status, previous_status,
            'The status of the request should not be changed.')
        eq_(self.foia.communications.count(), comm_count,
            'No communication should be added to the request.')


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
        nose.tools.eq_(self.foia.status, 'submitted',
            'The request should be set to processing.')
        nose.tools.eq_(self.foia.date_processing, datetime.date.today(),
            'The request should start tracking its days processing.')
        nose.tools.ok_(comm, 'The function should return a communication.')
        nose.tools.eq_(comm.delivered, 'mail', 'The communication should be mailed.')
        task = SnailMailTask.objects.filter(communication=comm).first()
        nose.tools.ok_(task, 'A snail mail task should be created.')
        nose.tools.eq_(task.user, user, 'The task should be attributed to the user.')
        nose.tools.eq_(task.amount, amount, 'The task should contain the amount of the request.')


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
        nose.tools.ok_(new_editor.has_perm('foia.change_foiarequest', self.foia))

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
        nose.tools.assert_true(viewer.has_perm('foia.view_foiarequest', embargoed_foia))
        nose.tools.assert_false(normie.has_perm('foia.view_foiarequest', embargoed_foia))

    def test_promote_viewer(self):
        """Editors should be able to promote viewers to editors."""
        embargoed_foia = FOIARequestFactory(embargo=True)
        viewer = UserFactory()
        embargoed_foia.add_viewer(viewer)
        nose.tools.assert_true(viewer.has_perm('foia.view_foiarequest', embargoed_foia))
        nose.tools.assert_false(viewer.has_perm('foia.change_foiarequest', embargoed_foia))
        embargoed_foia.promote_viewer(viewer)
        nose.tools.assert_true(viewer.has_perm('foia.change_foiarequest', embargoed_foia))

    def test_demote_editor(self):
        """Editors should be able to demote editors to viewers."""
        embargoed_foia = FOIARequestFactory(embargo=True)
        editor = UserFactory()
        embargoed_foia.add_editor(editor)
        nose.tools.assert_true(editor.has_perm('foia.view_foiarequest', embargoed_foia))
        nose.tools.assert_true(editor.has_perm('foia.change_foiarequest', embargoed_foia))
        embargoed_foia.demote_editor(editor)
        nose.tools.assert_false(editor.has_perm('foia.change_foiarequest', embargoed_foia))

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
        nose.tools.assert_true(self.creator.has_perm('foia.change_foiarequest', self.foia))
        nose.tools.assert_true(self.creator.has_perm('foia.view_foiarequest', self.foia))


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


class TestFOIANotification(TestCase):
    """The request should always notify its owner,
    but only notify followers if its not embargoed."""
    def setUp(self):
        agency = AgencyFactory()
        self.owner = UserFactory()
        self.follower = UserFactory()
        self.request = FOIARequestFactory(user=self.owner, agency=agency)
        follow(self.follower, self.request)
        self.action = new_action(agency, 'completed', target=self.request)

    def test_owner_notified(self):
        """The owner should always be notified."""
        # unembargoed
        notification_count = self.owner.notifications.count()
        self.request.notify(self.action)
        eq_(self.owner.notifications.count(), notification_count + 1,
            'The owner should get a new notification.')
        # embargoed
        self.request.embargo = True
        self.request.save()
        notification_count = self.owner.notifications.count()
        self.request.notify(self.action)
        eq_(self.owner.notifications.count(), notification_count + 1,
            'The owner should get a new notification.')

    def test_follower_notified(self):
        """The owner should always be notified."""
        # unembargoed
        notification_count = self.follower.notifications.count()
        self.request.notify(self.action)
        eq_(self.follower.notifications.count(), notification_count + 1,
            'A follower should get a new notification when unembargoed.')
        # embargoed
        self.request.embargo = True
        self.request.save()
        notification_count = self.follower.notifications.count()
        self.request.notify(self.action)
        eq_(self.follower.notifications.count(), notification_count,
            'A follower should not get a new notification when embargoed.')

    def test_identical_notification(self):
        """A new notification should mark any with identical language as read."""
        unread_count = self.owner.notifications.get_unread().count()
        self.request.notify(self.action)
        eq_(self.owner.notifications.get_unread().count(), unread_count + 1)
        unread_count = self.owner.notifications.get_unread().count()
        self.request.notify(self.action)
        eq_(self.owner.notifications.get_unread().count(), unread_count,
            'Any similar notifications should be marked as read.')

    def test_unidentical_notification(self):
        """A new notification shoudl not mark any with unidentical language as read."""
        first_action = new_action(self.request.agency, 'completed', target=self.request)
        second_action = new_action(self.request.agency, 'rejected', target=self.request)
        third_action = new_action(self.owner, 'completed', target=self.request)
        unread_count = self.owner.notifications.get_unread().count()
        self.request.notify(first_action)
        eq_(self.owner.notifications.get_unread().count(), unread_count + 1,
            'The user should have one unread notification.')
        self.request.notify(second_action)
        eq_(self.owner.notifications.get_unread().count(), unread_count + 2,
            'The user should have two unread notifications.')
        self.request.notify(third_action)
        eq_(self.owner.notifications.get_unread().count(), unread_count + 3,
            'The user should have three unread notifications.')

    def test_idential_different_requests(self):
        """An identical action on a different request should not mark anything as read."""
        other_request = FOIARequestFactory(user=self.owner, agency=self.request.agency)
        other_action = new_action(self.request.agency, 'completed', target=other_request)
        unread_count = self.owner.notifications.get_unread().count()
        self.request.notify(self.action)
        eq_(self.owner.notifications.get_unread().count(), unread_count + 1,
            'The user should have one unread notification.')
        other_request.notify(other_action)
        eq_(self.owner.notifications.get_unread().count(), unread_count + 2,
            'The user should have two unread notifications.')
