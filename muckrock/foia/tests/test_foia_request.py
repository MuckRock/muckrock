"""
Tests using nose for the FOIA application
"""

# Django
from django.contrib.auth.models import AnonymousUser, User
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import RequestFactory, TestCase
from django.utils import timezone

# Standard Library
import datetime
import re
from datetime import timedelta
from operator import attrgetter

# Third Party
import nose.tools
from actstream.actions import follow, is_following, unfollow
from freezegun import freeze_time
from nose.tools import (
    assert_false,
    assert_in,
    assert_is_none,
    assert_not_in,
    eq_,
    ok_,
)

# MuckRock
from muckrock.agency.models import Agency
from muckrock.factories import (
    AgencyFactory,
    AppealAgencyFactory,
    FOIACommunicationFactory,
    FOIARequestFactory,
    OrganizationFactory,
    ProjectFactory,
    UserFactory,
)
from muckrock.foia.models import FOIACommunication, FOIARequest
from muckrock.foia.views import (
    Detail,
    FollowingRequestList,
    MyRequestList,
    RequestList,
)
from muckrock.jurisdiction.factories import ExampleAppealFactory
from muckrock.jurisdiction.models import Appeal, Jurisdiction
from muckrock.project.forms import ProjectManagerForm
from muckrock.task.factories import ResponseTaskFactory
from muckrock.task.models import SnailMailTask, StatusChangeTask
from muckrock.test_utils import http_post_response
from muckrock.tests import (
    get_404,
    get_allowed,
    get_post_unallowed,
    post_allowed,
)
from muckrock.utils import new_action

# allow methods that could be functions and too many public methods in tests
# pylint: disable=too-many-public-methods
# pylint: disable=too-many-lines
# pylint: disable=invalid-name
# pylint: disable=bad-mcs-method-argument


class TestFOIARequestUnit(TestCase):
    """Unit tests for FOIARequests"""
    fixtures = [
        'holidays.json', 'jurisdictions.json', 'agency_types.json',
        'test_users.json', 'test_agencies.json', 'test_profiles.json',
        'test_foiarequests.json', 'test_foiacommunications.json', 'laws.json'
    ]

    def setUp(self):
        """Set up tests"""

        mail.outbox = []

        self.foia = FOIARequest.objects.get(pk=1)
        UserFactory(username='MuckrockStaff')

    # models
    def test_foia_model_unicode(self):
        """Test FOIA Request model's __unicode__ method"""
        nose.tools.eq_(unicode(self.foia), 'Test 1')

    def test_foia_model_url(self):
        """Test FOIA Request model's get_absolute_url method"""

        nose.tools.eq_(
            self.foia.get_absolute_url(),
            reverse(
                'foia-detail',
                kwargs={
                    'idx': self.foia.pk,
                    'slug': 'test-1',
                    'jurisdiction': 'massachusetts',
                    'jidx': self.foia.jurisdiction.pk
                }
            )
        )

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

        foias = list(
            FOIARequest.objects.filter(id__in=[1, 5, 11, 12, 13, 14]
                                       ).order_by('id')
        )
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

        # check manager get_viewable against view permission
        viewable_foias = FOIARequest.objects.get_viewable(user1)
        for foia in FOIARequest.objects.all():
            if foia in viewable_foias:
                nose.tools.assert_true(foia.has_perm(user1, 'view'))
            else:
                nose.tools.assert_false(foia.has_perm(user1, 'view'))

        viewable_foias = FOIARequest.objects.get_viewable(user2)
        for foia in FOIARequest.objects.all():
            if foia in viewable_foias:
                nose.tools.assert_true(foia.has_perm(user2, 'view'))
            else:
                nose.tools.assert_false(foia.has_perm(user2, 'view'))

        viewable_foias = FOIARequest.objects.get_public()
        for foia in FOIARequest.objects.all():
            if foia in viewable_foias:
                nose.tools.assert_true(foia.has_perm(AnonymousUser(), 'view'))
            else:
                nose.tools.assert_false(foia.has_perm(AnonymousUser(), 'view'))

        nose.tools.assert_true(foias[0].has_perm(user1, 'view'))
        nose.tools.assert_true(foias[1].has_perm(user1, 'view'))
        nose.tools.assert_true(foias[2].has_perm(user1, 'view'))
        nose.tools.assert_true(foias[3].has_perm(user1, 'view'))
        nose.tools.assert_true(foias[4].has_perm(user1, 'view'))

        nose.tools.assert_false(foias[0].has_perm(user2, 'view'))
        nose.tools.assert_true(foias[1].has_perm(user2, 'view'))
        nose.tools.assert_false(foias[2].has_perm(user2, 'view'))
        nose.tools.assert_true(foias[3].has_perm(user2, 'view'))
        nose.tools.assert_true(foias[4].has_perm(user2, 'view'))

        nose.tools.assert_false(foias[0].has_perm(AnonymousUser(), 'view'))
        nose.tools.assert_true(foias[1].has_perm(AnonymousUser(), 'view'))
        nose.tools.assert_false(foias[2].has_perm(AnonymousUser(), 'view'))
        nose.tools.assert_true(foias[3].has_perm(AnonymousUser(), 'view'))
        nose.tools.assert_true(foias[4].has_perm(AnonymousUser(), 'view'))

    def test_foia_viewable_org_share(self):
        """Test all the viewable and embargo functions"""
        org = OrganizationFactory()
        org.owner.profile.organization = org
        foia = FOIARequestFactory(
            embargo=True,
            user__profile__organization=org,
        )
        foias = FOIARequest.objects.get_viewable(org.owner)
        nose.tools.assert_not_in(foia, foias)

        foia.user.profile.org_share = True
        foia.user.profile.save()
        foias = FOIARequest.objects.get_viewable(org.owner)
        nose.tools.assert_in(foia, foias)

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
        foia = FOIARequestFactory(
            date_submitted=datetime.date.today(),
            status='processed',
            jurisdiction__level='s',
            jurisdiction__law__days=10,
        )
        FOIACommunicationFactory(
            foia=foia,
            response=True,
        )
        foia.followup()
        nose.tools.assert_in('I can expect', mail.outbox[-1].body)
        nose.tools.eq_(
            foia.date_followup,
            datetime.date.today() + datetime.timedelta(foia._followup_days())
        )

        nose.tools.eq_(foia._followup_days(), 15)

        num_days = 365
        foia.date_estimate = datetime.date.today(
        ) + datetime.timedelta(num_days)
        foia.followup()
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
        foia.date_estimate = datetime.date.today(
        ) + datetime.timedelta(num_days)
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
                    foia.status in [
                        'started', 'submitted', 'processed', 'fix', 'rejected',
                        'payment'
                    ]
                )


class TestFOIAFunctional(TestCase):
    """Functional tests for FOIA"""
    fixtures = [
        'holidays.json', 'jurisdictions.json', 'agency_types.json',
        'test_users.json', 'test_profiles.json', 'test_foiarequests.json',
        'test_foiacommunications.json', 'test_agencies.json', 'laws.json'
    ]

    def setUp(self):
        """Set up tests"""
        UserFactory(username='MuckrockStaff')

    # views
    def test_foia_list(self):
        """Test the foia-list view"""

        response = get_allowed(self.client, reverse('foia-list'))
        nose.tools.eq_(
            set(response.context['object_list']),
            set(
                FOIARequest.objects.get_viewable(AnonymousUser())
                .order_by('-date_submitted')[:12]
            )
        )

    def test_foia_list_user(self):
        """Test the foia-list-user view"""

        for user_pk in [1, 2]:
            response = get_allowed(
                self.client,
                reverse('foia-list-user', kwargs={
                    'user_pk': user_pk
                })
            )
            user = User.objects.get(pk=user_pk)
            nose.tools.eq_(
                set(response.context['object_list']),
                set(
                    FOIARequest.objects.get_viewable(AnonymousUser()
                                                     ).filter(user=user)
                )
            )
            nose.tools.ok_(
                all(
                    foia.user == user
                    for foia in response.context['object_list']
                )
            )

    def test_foia_sorted_list(self):
        """Test sorting on foia-list view"""

        for field in ['title', 'date_submitted']:
            for order in ['asc', 'desc']:
                response = get_allowed(
                    self.client,
                    reverse('foia-list') + '?sort=%s&order=%s' % (field, order)
                )
                nose.tools.eq_(
                    [f.title for f in response.context['object_list']], [
                        f.title for f in sorted(
                            response.context['object_list'],
                            key=attrgetter(field),
                            reverse=(order == 'desc')
                        )
                    ]
                )

    def test_foia_bad_sort(self):
        """Test sorting against a non-existant field"""
        response = get_allowed(self.client, reverse('foia-list') + '?sort=test')
        nose.tools.eq_(response.status_code, 200)

    def test_foia_detail(self):
        """Test the foia-detail view"""

        foia = FOIARequest.objects.get(pk=2)
        get_allowed(
            self.client,
            reverse(
                'foia-detail',
                kwargs={
                    'idx': foia.pk,
                    'slug': foia.slug,
                    'jurisdiction': foia.jurisdiction.slug,
                    'jidx': foia.jurisdiction.pk
                }
            )
        )

    def test_feeds(self):
        """Test the RSS feed views"""

        get_allowed(self.client, reverse('foia-submitted-feed'))
        get_allowed(self.client, reverse('foia-done-feed'))

    def test_404_views(self):
        """Test views that should give a 404 error"""

        get_404(
            self.client,
            reverse(
                'foia-detail',
                kwargs={
                    'idx': 1,
                    'slug': 'test-c',
                    'jurisdiction': 'massachusetts',
                    'jidx': 1
                }
            )
        )
        get_404(
            self.client,
            reverse(
                'foia-detail',
                kwargs={
                    'idx': 2,
                    'slug': 'test-c',
                    'jurisdiction': 'massachusetts',
                    'jidx': 1
                }
            )
        )

    def test_unallowed_views(self):
        """Test private views while not logged in"""

        foia = FOIARequest.objects.get(pk=2)
        get_post_unallowed(
            self.client,
            reverse(
                'foia-draft',
                kwargs={
                    'jurisdiction': foia.jurisdiction.slug,
                    'jidx': foia.jurisdiction.pk,
                    'idx': foia.pk,
                    'slug': foia.slug
                }
            )
        )

    def test_auth_views(self):
        """Test private views while logged in"""

        foia = FOIARequestFactory(status='started')
        self.client.login(username='adam', password='abc')

        # get authenticated pages
        get_allowed(self.client, reverse('foia-create'))

        get_allowed(
            self.client,
            reverse(
                'foia-draft',
                kwargs={
                    'jurisdiction': foia.jurisdiction.slug,
                    'jidx': foia.jurisdiction.pk,
                    'idx': foia.pk,
                    'slug': foia.slug
                }
            )
        )

        get_404(
            self.client,
            reverse(
                'foia-draft',
                kwargs={
                    'jurisdiction': foia.jurisdiction.slug,
                    'jidx': foia.jurisdiction.pk,
                    'idx': foia.pk,
                    'slug': 'bad_slug'
                }
            )
        )

    def test_foia_submit_views(self):
        """Test submitting a FOIA request"""

        foia = FOIARequestFactory(
            status='started',
            user=User.objects.get(username='adam'),
        )
        FOIACommunicationFactory(foia=foia)
        self.client.login(username='adam', password='abc')

        foia_data = {
            'title': foia.title,
            'request': 'updated request',
            'submit': 'Submit',
            'agency': foia.agency.pk,
            'combo-name': foia.agency.name,
        }
        kwargs = {
            'jurisdiction': foia.jurisdiction.slug,
            'jidx': foia.jurisdiction.pk,
            'idx': foia.pk,
            'slug': foia.slug,
        }
        draft = reverse('foia-draft', kwargs=kwargs)
        detail = reverse('foia-detail', kwargs=kwargs)
        post_allowed(self.client, draft, foia_data, detail)

        foia.refresh_from_db()
        nose.tools.ok_(foia.first_request().startswith('updated request'))
        nose.tools.eq_(foia.status, 'ack')

    def test_foia_save_views(self):
        """Test saving a FOIA request"""

        foia = FOIARequest.objects.get(pk=6)
        self.client.login(username='bob', password='abc')

        foia_data = {
            'title': 'Test 6',
            'request': 'saved request',
            'submit': 'Save'
        }

        kwargs = {
            'jurisdiction': foia.jurisdiction.slug,
            'jidx': foia.jurisdiction.pk,
            'idx': foia.pk,
            'slug': foia.slug
        }
        draft = reverse(
            'foia-draft', kwargs=kwargs
        ).replace('http://testserver', '')
        detail = reverse(
            'foia-detail', kwargs=kwargs
        ).replace('http://testserver', '')
        chain = [(url, 302) for url in (detail, draft)]
        response = self.client.post(draft, foia_data, follow=True)
        nose.tools.eq_(response.status_code, 200)
        nose.tools.eq_(response.redirect_chain, chain)

        foia = FOIARequest.objects.get(title='Test 6')
        nose.tools.ok_(foia.first_request().startswith('saved request'))
        nose.tools.eq_(foia.status, 'started')

    def test_action_views(self):
        """Test action views"""

        self.client.login(username='adam', password='abc')

        foia = FOIARequestFactory(status='payment')
        get_allowed(
            self.client,
            reverse(
                'foia-pay',
                kwargs={
                    'jurisdiction': foia.jurisdiction.slug,
                    'jidx': foia.jurisdiction.pk,
                    'idx': foia.pk,
                    'slug': foia.slug
                }
            )
        )


class TestFOIAIntegration(TestCase):
    """Integration tests for FOIA"""

    fixtures = [
        'holidays.json', 'jurisdictions.json', 'agency_types.json',
        'test_users.json', 'test_agencies.json', 'test_profiles.json',
        'test_foiarequests.json', 'test_foiacommunications.json', 'laws.json'
    ]

    def setUp(self):
        """Set up tests"""
        mail.outbox = []

    def test_request_lifecycle_no_email(self):
        """Test a request going through the full cycle as if we had to physically mail it"""
        # pylint: disable=too-many-statements
        # pylint: disable=protected-access

        user = User.objects.get(username='adam')
        agency = Agency.objects.get(pk=3)
        jurisdiction = Jurisdiction.objects.get(pk=1)
        cal = jurisdiction.get_calendar()

        with freeze_time("2010-02-01"):
            nose.tools.eq_(len(mail.outbox), 0)

            ## create and submit request
            foia = FOIARequest.objects.create(
                user=user,
                title='Test with no email',
                slug='test-with-no-email',
                status='submitted',
                jurisdiction=jurisdiction,
                agency=agency,
            )
            comm = FOIACommunication.objects.create(
                foia=foia,
                from_user=user,
                to_user=agency.get_user(),
                date=timezone.now(),
                response=False,
                communication=u'Test communication',
            )
            foia.submit()

            # check that a snail mail task was created
            nose.tools.ok_(
                SnailMailTask.objects.filter(communication=comm,
                                             category='n').exists()
            )

        ## two days pass, then the admin mails in the request
        with freeze_time("2010-02-03"):
            foia.status = 'processed'
            foia.update_dates()
            foia.save()

            # make sure dates were set correctly
            nose.tools.eq_(foia.date_submitted, datetime.date(2010, 2, 1))
            nose.tools.eq_(
                foia.date_due,
                cal.business_days_from(
                    datetime.date(2010, 2, 1),
                    jurisdiction.days,
                )
            )
            nose.tools.eq_(
                foia.date_followup,
                max(
                    foia.date_due,
                    foia.last_comm().date.date() +
                    datetime.timedelta(foia._followup_days())
                )
            )
            nose.tools.ok_(foia.days_until_due is None)
            # no more mail should have been sent
            nose.tools.eq_(len(mail.outbox), 0)

            old_date_due = foia.date_due

        ## after 5 days agency replies with a fix needed
        with freeze_time("2010-02-08"):
            comm = FOIACommunication.objects.create(
                foia=foia,
                from_user=agency.get_user(),
                to_user=user,
                date=timezone.now(),
                response=True,
                communication='Test communication',
            )
            foia.status = 'fix'
            foia.save()
            foia.update(comm.anchor())

            # make sure dates were set correctly
            nose.tools.eq_(foia.date_submitted, datetime.date(2010, 2, 1))
            nose.tools.ok_(foia.date_due is None)
            nose.tools.ok_(foia.date_followup is None)
            nose.tools.eq_(
                foia.days_until_due,
                cal.business_days_between(
                    datetime.date(2010, 2, 8), old_date_due
                )
            )

            old_days_until_due = foia.days_until_due

        ## after 10 days the user submits the fix and the admin submits it right away
        with freeze_time("2010-02-18"):
            comm = FOIACommunication.objects.create(
                foia=foia,
                from_user=user,
                to_user=agency.get_user(),
                date=timezone.now(),
                response=False,
                communication='Test communication',
            )
            foia.status = 'submitted'
            foia.save()
            foia.submit()

            # check that another snail mail task is created
            nose.tools.ok_(
                SnailMailTask.objects.filter(communication=comm,
                                             category='u').exists()
            )

            foia.status = 'processed'

            foia.update_dates()
            foia.save()

            # make sure dates were set correctly
            nose.tools.eq_(foia.date_submitted, datetime.date(2010, 2, 1))
            nose.tools.eq_(
                foia.date_due,
                cal.business_days_from(
                    datetime.date.today(), old_days_until_due
                )
            )
            nose.tools.eq_(
                foia.date_followup,
                max(
                    foia.date_due,
                    foia.last_comm().date.date() +
                    datetime.timedelta(foia._followup_days())
                )
            )
            nose.tools.ok_(foia.days_until_due is None)

            old_date_due = foia.date_due

        ## after 4 days agency replies with the documents
        with freeze_time("2010-02-22"):
            comm = FOIACommunication.objects.create(
                foia=foia,
                from_user=agency.get_user(),
                to_user=user,
                date=timezone.now(),
                response=True,
                communication='Test communication',
            )
            foia.status = 'done'
            foia.save()
            foia.update(comm.anchor())

            # make sure dates were set correctly
            nose.tools.eq_(foia.date_submitted, datetime.date(2010, 2, 1))
            nose.tools.eq_(foia.date_due, old_date_due)
            nose.tools.ok_(foia.date_followup is None)
            nose.tools.ok_(foia.days_until_due is None)


class TestFOIARequestAppeal(TestCase):
    """A request should be able to send an appeal to the agency that receives them."""

    def setUp(self):
        self.appeal_agency = AppealAgencyFactory()
        self.agency = AgencyFactory(
            status='approved', appeal_agency=self.appeal_agency
        )
        self.foia = FOIARequestFactory(agency=self.agency, status='rejected')

    def test_appeal(self):
        """Sending an appeal to the agency should require the message for the appeal,
        which is then turned into a communication to the correct agency. In this case,
        the correct agency is the same one that received the message."""
        ok_(
            self.foia.has_perm(self.foia.user, 'appeal'),
            'The request should be appealable.'
        )
        ok_(
            self.agency and self.agency.status == 'approved',
            'The agency should be approved.'
        )
        ok_(
            self.appeal_agency.get_emails('appeal'),
            'The appeal agency should accept email.'
        )
        # Create the appeal message and submit it
        appeal_message = 'Lorem ipsum'
        appeal_comm = self.foia.appeal(appeal_message, self.foia.user)
        # Check that everything happened like we expected
        self.foia.refresh_from_db()
        appeal_comm.refresh_from_db()
        eq_(self.foia.email, self.appeal_agency.get_emails('appeal').first())
        eq_(self.foia.status, 'appealing')
        eq_(appeal_comm.communication, appeal_message)
        eq_(appeal_comm.from_user, self.foia.user)
        eq_(appeal_comm.to_user, self.agency.get_user())
        ok_(appeal_comm.emails.exists())

    def test_mailed_appeal(self):
        """Sending an appeal to an agency via mail should set the request to 'submitted',
        create a snail mail task with the 'a' category, and set the appeal communication
        delivery method to 'mail'."""
        # Make the appeal agency unreceptive to emails
        self.appeal_agency.emails.clear()
        # Create the appeal message and submit it
        appeal_message = 'Lorem ipsum'
        appeal_comm = self.foia.appeal(appeal_message, self.foia.user)
        # Check that everything happened like we expected
        self.foia.refresh_from_db()
        appeal_comm.refresh_from_db()
        eq_(
            self.foia.status, 'submitted',
            'The status of the request should be updated. Actually: %s' %
            self.foia.status
        )
        eq_(
            appeal_comm.communication, appeal_message,
            'The appeal message parameter should be used as the body of the communication.'
        )
        eq_(
            appeal_comm.from_user, self.foia.user,
            'The appeal should be addressed from the request owner.'
        )
        eq_(
            appeal_comm.to_user, self.agency.get_user(),
            'The appeal should be addressed to the agency.'
        )
        task = SnailMailTask.objects.get(communication=appeal_comm)
        ok_(task, 'A snail mail task should be created.')
        eq_(task.category, 'a')


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
        UserFactory(username='MuckrockStaff')

    def test_add_tags(self):
        """Posting a collection of tags to a request should update its tags."""
        data = {'action': 'tags', 'tags': 'foo, bar'}
        http_post_response(
            self.url, self.view, data, self.foia.user, **self.kwargs
        )
        self.foia.refresh_from_db()
        ok_('foo' in [tag.name for tag in self.foia.tags.all()])
        ok_('bar' in [tag.name for tag in self.foia.tags.all()])

    def test_add_projects(self):
        """Posting a collection of projects to a request should add it to those projects."""
        project = ProjectFactory()
        project.contributors.add(self.foia.user)
        form = ProjectManagerForm({
            'projects': [project.pk]
        },
                                  user=self.foia.user)
        ok_(form.is_valid())
        data = {'action': 'projects'}
        data.update(form.data)
        http_post_response(
            self.url, self.view, data, self.foia.user, **self.kwargs
        )
        project.refresh_from_db()
        ok_(self.foia in project.requests.all())

    def test_appeal(self):
        """Appealing a request should send a new communication,
        record the details of the appeal, and update the status of the request."""
        comm_count = self.foia.communications.count()
        data = {'action': 'appeal', 'text': 'Lorem ipsum'}
        http_post_response(
            self.url, self.view, data, self.foia.user, **self.kwargs
        )
        self.foia.refresh_from_db()
        eq_(self.foia.status, 'appealing')
        eq_(self.foia.communications.count(), comm_count + 1)
        eq_(
            self.foia.last_comm().communication, data['text'],
            'The appeal should use the language provided by the user.'
        )
        appeal = Appeal.objects.last()
        ok_(appeal, 'An Appeal object should be created.')
        eq_(
            self.foia.last_comm(), appeal.communication,
            'The appeal should reference the communication that was created.'
        )

    def test_appeal_example(self):
        """If an example appeal is used to base the appeal off of,
        then the examples should be recorded to the appeal object as well."""
        example_appeal = ExampleAppealFactory()
        data = {
            'action': 'appeal',
            'text': 'Lorem ipsum',
            'base_language': example_appeal.pk
        }
        http_post_response(
            self.url, self.view, data, self.foia.user, **self.kwargs
        )
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
        http_post_response(
            self.url, self.view, data, unauth_user, **self.kwargs
        )
        self.foia.refresh_from_db()
        eq_(
            self.foia.status, previous_status,
            'The status of the request should not be changed.'
        )
        eq_(
            self.foia.communications.count(), comm_count,
            'No communication should be added to the request.'
        )

    def test_missing_appeal(self):
        """An appeal that is missing its language should not do anything."""
        comm_count = self.foia.communications.count()
        previous_status = self.foia.status
        data = {'action': 'appeal', 'text': ''}
        http_post_response(
            self.url, self.view, data, self.foia.user, **self.kwargs
        )
        self.foia.refresh_from_db()
        eq_(
            self.foia.status, previous_status,
            'The status of the request should not be changed.'
        )
        eq_(
            self.foia.communications.count(), comm_count,
            'No communication should be added to the request.'
        )

    def test_unappealable_request(self):
        """An appeal on a request that cannot be appealed should not do anything."""
        self.foia.status = 'submitted'
        self.foia.save()
        nose.tools.assert_false(self.foia.has_perm(self.foia.user, 'appeal'))
        comm_count = self.foia.communications.count()
        previous_status = self.foia.status
        data = {'action': 'appeal', 'text': 'Lorem ipsum'}
        http_post_response(
            self.url, self.view, data, self.foia.user, **self.kwargs
        )
        self.foia.refresh_from_db()
        eq_(
            self.foia.status, previous_status,
            'The status of the request should not be changed.'
        )
        eq_(
            self.foia.communications.count(), comm_count,
            'No communication should be added to the request.'
        )

    def test_post_status(self):
        """A user updating the status of their request should update the status,
        open a status change task, and close any open response tasks"""
        nose.tools.assert_not_equal(self.foia.status, 'done')
        eq_(
            len(
                StatusChangeTask.objects.filter(
                    foia=self.foia,
                    user=self.foia.user,
                    resolved=False,
                )
            ), 0
        )
        communication = FOIACommunicationFactory(foia=self.foia)
        response_task = ResponseTaskFactory(
            communication=communication,
            resolved=False,
        )
        data = {'action': 'status', 'status': 'done'}
        http_post_response(
            self.url, self.view, data, self.foia.user, **self.kwargs
        )
        self.foia.refresh_from_db()
        eq_(self.foia.status, 'done')
        eq_(
            len(
                StatusChangeTask.objects.filter(
                    foia=self.foia,
                    user=self.foia.user,
                    resolved=False,
                )
            ), 1
        )
        response_task.refresh_from_db()
        ok_(response_task.resolved)


class TestFollowingRequestList(TestCase):
    """Test to make sure following request list shows correct requests"""

    def test_following_request_list(self):
        """Test to make sure following request list shows correct requests"""
        user = UserFactory()
        factory = RequestFactory()
        request = factory.get(reverse('foia-list-following'))
        request.user = user
        foias = FOIARequestFactory.create_batch(7)
        for foia in foias[::2]:
            follow(user, foia)
        response = FollowingRequestList.as_view()(request)
        eq_(len(response.context_data['object_list']), 4)
        for foia in foias[::2]:
            nose.tools.assert_in(foia, response.context_data['object_list'])

        unfollow(user, foias[2])
        response = FollowingRequestList.as_view()(request)
        eq_(len(response.context_data['object_list']), 3)
        for foia in (foias[0], foias[4], foias[6]):
            nose.tools.assert_in(foia, response.context_data['object_list'])


class TestRequestPayment(TestCase):
    """Allow users to pay fees on a request"""

    def setUp(self):
        self.foia = FOIARequestFactory()
        UserFactory(username='MuckrockStaff')

    def test_make_payment(self):
        """The request should accept payments for request fees."""
        user = self.foia.user
        amount = 100.0
        comm = self.foia.pay(user, amount)
        self.foia.refresh_from_db()
        eq_(self.foia.status, 'submitted')
        eq_(self.foia.date_processing, datetime.date.today())
        ok_(comm, 'The function should return a communication.')
        task = SnailMailTask.objects.filter(communication=comm).first()
        ok_(task, 'A snail mail task should be created.')
        eq_(task.user, user)
        eq_(task.amount, amount)


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
        nose.tools.ok_(self.foia.has_perm(new_editor, 'change'))

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
        nose.tools.assert_true(embargoed_foia.has_perm(viewer, 'view'))
        nose.tools.assert_false(embargoed_foia.has_perm(normie, 'view'))

    def test_promote_viewer(self):
        """Editors should be able to promote viewers to editors."""
        embargoed_foia = FOIARequestFactory(embargo=True)
        viewer = UserFactory()
        embargoed_foia.add_viewer(viewer)
        nose.tools.assert_true(embargoed_foia.has_perm(viewer, 'view'))
        nose.tools.assert_false(embargoed_foia.has_perm(viewer, 'change'))
        embargoed_foia.promote_viewer(viewer)
        nose.tools.assert_true(embargoed_foia.has_perm(viewer, 'change'))

    def test_demote_editor(self):
        """Editors should be able to demote editors to viewers."""
        embargoed_foia = FOIARequestFactory(embargo=True)
        editor = UserFactory()
        embargoed_foia.add_editor(editor)
        nose.tools.assert_true(embargoed_foia.has_perm(editor, 'view'))
        nose.tools.assert_true(embargoed_foia.has_perm(editor, 'change'))
        embargoed_foia.demote_editor(editor)
        nose.tools.assert_false(embargoed_foia.has_perm(editor, 'change'))

    def test_access_key(self):
        """Editors should be able to generate a secure access key to view an embargoed request."""
        embargoed_foia = FOIARequestFactory(embargo=True)
        access_key = embargoed_foia.generate_access_key()
        nose.tools.assert_true(
            access_key == embargoed_foia.access_key,
            'The key in the URL should match the key saved to the request.'
        )
        embargoed_foia.generate_access_key()
        nose.tools.assert_false(
            access_key == embargoed_foia.access_key,
            'After regenerating the link, the key should no longer match.'
        )

    def test_do_not_grant_creator_access(self):
        """Creators should not be granted access as editors or viewers"""
        self.foia.add_editor(self.creator)
        nose.tools.assert_false(self.foia.has_editor(self.creator))
        self.foia.add_viewer(self.creator)
        nose.tools.assert_false(self.foia.has_viewer(self.creator))
        # but the creator should still be able to both view and edit!
        nose.tools.assert_true(self.foia.has_perm(self.creator, 'change'))
        nose.tools.assert_true(self.foia.has_perm(self.creator, 'view'))


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
        eq_(
            self.owner.notifications.count(), notification_count + 1,
            'The owner should get a new notification.'
        )
        # embargoed
        self.request.embargo = True
        self.request.save()
        notification_count = self.owner.notifications.count()
        self.request.notify(self.action)
        eq_(
            self.owner.notifications.count(), notification_count + 1,
            'The owner should get a new notification.'
        )

    def test_follower_notified(self):
        """The owner should always be notified."""
        # unembargoed
        notification_count = self.follower.notifications.count()
        self.request.notify(self.action)
        eq_(
            self.follower.notifications.count(), notification_count + 1,
            'A follower should get a new notification when unembargoed.'
        )
        # embargoed
        self.request.embargo = True
        self.request.save()
        notification_count = self.follower.notifications.count()
        self.request.notify(self.action)
        eq_(
            self.follower.notifications.count(), notification_count,
            'A follower should not get a new notification when embargoed.'
        )

    def test_identical_notification(self):
        """A new notification should mark any with identical language as read."""
        unread_count = self.owner.notifications.get_unread().count()
        self.request.notify(self.action)
        eq_(self.owner.notifications.get_unread().count(), unread_count + 1)
        unread_count = self.owner.notifications.get_unread().count()
        self.request.notify(self.action)
        eq_(
            self.owner.notifications.get_unread().count(), unread_count,
            'Any similar notifications should be marked as read.'
        )

    def test_unidentical_notification(self):
        """A new notification shoudl not mark any with unidentical language as read."""
        first_action = new_action(
            self.request.agency, 'completed', target=self.request
        )
        second_action = new_action(
            self.request.agency, 'rejected', target=self.request
        )
        third_action = new_action(self.owner, 'completed', target=self.request)
        unread_count = self.owner.notifications.get_unread().count()
        self.request.notify(first_action)
        eq_(
            self.owner.notifications.get_unread().count(), unread_count + 1,
            'The user should have one unread notification.'
        )
        self.request.notify(second_action)
        eq_(
            self.owner.notifications.get_unread().count(), unread_count + 2,
            'The user should have two unread notifications.'
        )
        self.request.notify(third_action)
        eq_(
            self.owner.notifications.get_unread().count(), unread_count + 3,
            'The user should have three unread notifications.'
        )

    def test_idential_different_requests(self):
        """An identical action on a different request should not mark anything as read."""
        other_request = FOIARequestFactory(
            user=self.owner, agency=self.request.agency
        )
        other_action = new_action(
            self.request.agency, 'completed', target=other_request
        )
        unread_count = self.owner.notifications.get_unread().count()
        self.request.notify(self.action)
        eq_(
            self.owner.notifications.get_unread().count(), unread_count + 1,
            'The user should have one unread notification.'
        )
        other_request.notify(other_action)
        eq_(
            self.owner.notifications.get_unread().count(), unread_count + 2,
            'The user should have two unread notifications.'
        )


class TestBulkActions(TestCase):
    """Test the bulk actions on the list views"""

    # pylint: disable=protected-access

    def test_follow(self):
        """Test bulk following"""
        public_foia = FOIARequestFactory()
        private_foia = FOIARequestFactory(embargo=True)
        user = UserFactory()

        RequestList()._follow(
            FOIARequest.objects.filter(
                pk__in=[public_foia.pk, private_foia.pk]
            ),
            user,
            {},
        )

        ok_(is_following(user, public_foia))
        assert_false(is_following(user, private_foia))

    def test_unfollow(self):
        """Test bulk unfollowing"""
        follow_foia = FOIARequestFactory()
        unfollow_foia = FOIARequestFactory()
        user = UserFactory()

        follow(user, follow_foia, actor_only=False)

        RequestList()._unfollow(
            FOIARequest.objects.filter(
                pk__in=[follow_foia.pk, unfollow_foia.pk]
            ),
            user,
            {},
        )

        assert_false(is_following(user, follow_foia))
        assert_false(is_following(user, unfollow_foia))

    def test_extend_embargo(self):
        """Test bulk embargo extending"""
        tomorrow = datetime.date.today() + timedelta(1)
        next_month = datetime.date.today() + timedelta(30)
        user = UserFactory(profile__acct_type='pro')
        other_foia = FOIARequestFactory()
        public_foia = FOIARequestFactory(user=user, embargo=False, status='ack')
        embargo_foia = FOIARequestFactory(user=user, embargo=True, status='ack')
        embargo_done_foia = FOIARequestFactory(
            user=user,
            embargo=True,
            status='done',
            date_embargo=tomorrow,
        )

        MyRequestList()._extend_embargo(
            FOIARequest.objects.filter(
                pk__in=[
                    other_foia.pk,
                    public_foia.pk,
                    embargo_foia.pk,
                    embargo_done_foia.pk,
                ]
            ),
            user,
            {},
        )

        other_foia.refresh_from_db()
        public_foia.refresh_from_db()
        embargo_foia.refresh_from_db()
        embargo_done_foia.refresh_from_db()

        assert_false(other_foia.embargo)
        ok_(public_foia.embargo)
        assert_is_none(public_foia.date_embargo)
        ok_(embargo_foia.embargo)
        assert_is_none(embargo_foia.date_embargo)
        ok_(embargo_done_foia.embargo)
        eq_(embargo_done_foia.date_embargo, next_month)

    def test_remove_embargo(self):
        """Test bulk embargo removing"""
        tomorrow = datetime.date.today() + timedelta(1)
        user = UserFactory(profile__acct_type='pro')
        other_foia = FOIARequestFactory()
        public_foia = FOIARequestFactory(user=user, embargo=False, status='ack')
        embargo_foia = FOIARequestFactory(user=user, embargo=True, status='ack')
        embargo_done_foia = FOIARequestFactory(
            user=user,
            embargo=True,
            status='done',
            date_embargo=tomorrow,
        )

        MyRequestList()._remove_embargo(
            FOIARequest.objects.filter(
                pk__in=[
                    other_foia.pk,
                    public_foia.pk,
                    embargo_foia.pk,
                    embargo_done_foia.pk,
                ]
            ),
            user,
            {},
        )

        other_foia.refresh_from_db()
        public_foia.refresh_from_db()
        embargo_foia.refresh_from_db()
        embargo_done_foia.refresh_from_db()

        assert_false(other_foia.embargo)
        assert_false(public_foia.embargo)
        assert_false(embargo_foia.embargo)
        assert_false(embargo_done_foia.embargo)

    def test_perm_embargo(self):
        """Test bulk permanent embargo"""
        tomorrow = datetime.date.today() + timedelta(1)
        user = UserFactory(profile__acct_type='admin')
        other_foia = FOIARequestFactory()
        public_foia = FOIARequestFactory(user=user, embargo=False, status='ack')
        embargo_foia = FOIARequestFactory(user=user, embargo=True, status='ack')
        embargo_done_foia = FOIARequestFactory(
            user=user,
            embargo=True,
            status='done',
            date_embargo=tomorrow,
        )

        MyRequestList()._perm_embargo(
            FOIARequest.objects.filter(
                pk__in=[
                    other_foia.pk,
                    public_foia.pk,
                    embargo_foia.pk,
                    embargo_done_foia.pk,
                ]
            ),
            user,
            {},
        )

        other_foia.refresh_from_db()
        public_foia.refresh_from_db()
        embargo_foia.refresh_from_db()
        embargo_done_foia.refresh_from_db()

        assert_false(other_foia.embargo)
        ok_(public_foia.embargo)
        assert_false(public_foia.permanent_embargo)
        ok_(embargo_foia.embargo)
        assert_false(embargo_foia.permanent_embargo)
        ok_(embargo_done_foia.embargo)
        ok_(embargo_done_foia.permanent_embargo)

    def test_projects(self):
        """Test bulk add to projects"""
        user = UserFactory()
        foia = FOIARequestFactory(user=user)
        proj = ProjectFactory()
        proj.contributors.add(user)

        MyRequestList()._project(
            FOIARequest.objects.filter(pk=foia.pk),
            user,
            {'projects': [proj.pk]},
        )

        foia.refresh_from_db()

        assert_in(proj, foia.projects.all())

    def test_tags(self):
        """Test bulk add tags"""
        user = UserFactory()
        foia = FOIARequestFactory(user=user)

        MyRequestList()._tags(
            FOIARequest.objects.filter(pk=foia.pk),
            user,
            {'tags': 'red, blue'},
        )

        foia.refresh_from_db()

        tags = [t.name for t in foia.tags.all()]

        assert_in('red', tags)
        assert_in('blue', tags)

    def test_share(self):
        """Test bulk sharing"""
        user = UserFactory()
        share_user = UserFactory()
        foia = FOIARequestFactory(user=user)

        MyRequestList()._share(
            FOIARequest.objects.filter(pk=foia.pk),
            user,
            {'access': 'edit',
             'users': [share_user.pk]},
        )

        foia.refresh_from_db()

        assert_in(share_user, foia.edit_collaborators.all())
        assert_not_in(share_user, foia.read_collaborators.all())

    def test_autofollowup_on(self):
        """Test bulk autofollowup enabling"""
        user = UserFactory()
        on_foia = FOIARequestFactory(user=user, disable_autofollowups=False)
        off_foia = FOIARequestFactory(user=user, disable_autofollowups=True)

        MyRequestList()._autofollowup_on(
            FOIARequest.objects.filter(pk__in=[on_foia.pk, off_foia.pk]),
            user,
            {},
        )

        on_foia.refresh_from_db()
        off_foia.refresh_from_db()

        assert_false(on_foia.disable_autofollowups)
        assert_false(off_foia.disable_autofollowups)

    def test_autofollowup_off(self):
        """Test bulk autofollowup disabling"""
        user = UserFactory()
        on_foia = FOIARequestFactory(user=user, disable_autofollowups=False)
        off_foia = FOIARequestFactory(user=user, disable_autofollowups=True)

        MyRequestList()._autofollowup_off(
            FOIARequest.objects.filter(pk__in=[on_foia.pk, off_foia.pk]),
            user,
            {},
        )

        on_foia.refresh_from_db()
        off_foia.refresh_from_db()

        ok_(on_foia.disable_autofollowups)
        ok_(off_foia.disable_autofollowups)
