"""
Tests for Agency application
"""

from django.core.urlresolvers import reverse
from django.http import Http404
from django.test import TestCase

from datetime import datetime, timedelta
import nose.tools

from muckrock import agency
from muckrock import factories
from muckrock.task.models import StaleAgencyTask
from muckrock.task.factories import StaleAgencyTaskFactory
from muckrock.test_utils import http_get_response

ok_ = nose.tools.ok_
eq_ = nose.tools.eq_


class TestAgencyUnit(TestCase):
    """Unit tests for Agencies"""

    def setUp(self):
        """Set up tests"""
        self.agency1 = factories.AgencyFactory(
                fax__phone__number='1-987-654-3211',
                email__email__email='test@agency1.gov',
                other_emails='other_a@agency1.gov, other_b@agency1.gov'
                )
        self.agency2 = factories.AgencyFactory(
                fax__phone__number='987.654.3210',
                )
        self.agency3 = factories.AgencyFactory(
                email=None,
                )

    def test_agency_url(self):
        """Test Agency model's get_absolute_url method"""
        eq_(self.agency1.get_absolute_url(), reverse('agency-detail', kwargs={
                'idx': self.agency1.pk,
                'slug': self.agency1.slug,
                'jurisdiction': self.agency1.jurisdiction.slug,
                'jidx': self.agency1.jurisdiction.pk
            })
        )

    def test_agency_get_email(self):
        """Test the get emails method"""
        eq_(self.agency1.get_emails().first().email, 'test@agency1.gov')
        eq_(self.agency3.get_emails().first(), None)

    def test_agency_get_faxes(self):
        """Test the ganecy get faces method"""
        eq_(self.agency2.get_faxes().first().number, '19876543210')

    def test_agency_get_other_emails(self):
        """Test get other emails method"""
        eq_(
                set(e.email for e in self.agency1.get_emails(email_type='cc')),
                set(['other_a@agency1.gov', 'other_b@agency1.gov']),
                )

    def test_agency_is_stale(self):
        """Should return the date of the last response by the agency"""
        duration = agency.models.STALE_DURATION + 1
        comm_date = datetime.today() - timedelta(duration)
        factories.FOIACommunicationFactory(
            date=comm_date,
            response=True,
            foia__status='ack',
            foia__agency=self.agency1
        )
        eq_(self.agency1.is_stale(), True,
            "The agency should report the days since its latest response.")

    def test_agency_mark_stale(self):
        """Should mark the agency as stale and return a stale agency task,
        creating the task if one doesn't already exist."""
        ok_(not StaleAgencyTask.objects.filter(resolved=False, agency=self.agency1).exists(),
            'There should not be any unresolved StaleAgencyTasks for this request.')
        task = self.agency1.mark_stale()
        ok_(self.agency1.stale,
            'The agency should be marked as stale.')
        ok_(not self.agency1.manual_stale,
            'The agency should not be marked as manually stale.')
        ok_(isinstance(task, StaleAgencyTask),
            'A StaleAgencyTask should be returned.')
        second_task = self.agency1.mark_stale()
        eq_(task, second_task,
            'Instead of creating another task, return the one that already exists.')

    def test_agency_manual_stale(self):
        """Should be able to manually mark an agency as stale."""
        self.agency1.mark_stale(manual=True)
        ok_(self.agency1.stale,
            'The agency should be marked as stale.')
        ok_(self.agency1.manual_stale,
            'The agency should be marked as manually stale.')
        ok_(self.agency1.is_stale(),
            'An agency that is manually stale should always be stale.')

    def test_agency_multiple_tasks(self):
        """If multiple StaleAgencyTasks exist, only the first should be returned
        when marking an agency as stale."""
        stale_agency_tasks = [
            StaleAgencyTaskFactory(agency=self.agency1),
            StaleAgencyTaskFactory(agency=self.agency1),
            StaleAgencyTaskFactory(agency=self.agency1),
        ]
        task = self.agency1.mark_stale()
        eq_(task, stale_agency_tasks[0],
            'The returned task should be the first stale agency task.')

    def test_agency_unmark_stale(self):
        """Unmark the agency as stale."""
        # first mark it as stale
        self.agency1.mark_stale(manual=True)
        # then unmark it as stale
        self.agency1.unmark_stale()
        ok_(not self.agency1.stale,
            'The agency should no longer be marked as stale.')
        ok_(not self.agency1.manual_stale,
            'A manually stale agency should also be freed from staleness.')


class TestAgencyManager(TestCase):
    """Tests for the Agency object manager"""
    def setUp(self):
        self.agency1 = factories.AgencyFactory()
        self.agency2 = factories.AgencyFactory(
                jurisdiction=self.agency1.jurisdiction)
        self.agency3 = factories.AgencyFactory(
                jurisdiction=self.agency1.jurisdiction,
                status='pending')

    def test_get_approved(self):
        """Manager should return all approved agencies"""
        agencies = agency.models.Agency.objects.get_approved()
        ok_(self.agency1 in agencies)
        ok_(self.agency2 in agencies)
        ok_(self.agency3 not in agencies)

    def test_get_siblings(self):
        """Manager should return all siblings to a given agency"""
        agencies = agency.models.Agency.objects.get_siblings(self.agency1)
        ok_(self.agency1 not in agencies, 'The given agency shouldn\'t be its own sibling.')
        ok_(self.agency2 in agencies)
        ok_(self.agency3 not in agencies, 'Unapproved agencies shouldn\'t be siblings.')


class TestAgencyViews(TestCase):
    """Tests for Agency views"""
    def setUp(self):
        self.agency = factories.AgencyFactory()
        self.url = self.agency.get_absolute_url()
        self.view = agency.views.detail
        self.user = factories.UserFactory()
        self.kwargs = {
            'jurisdiction': self.agency.jurisdiction.slug,
            'jidx': self.agency.jurisdiction.id,
            'slug': self.agency.slug,
            'idx': self.agency.id
        }

    def test_approved_ok(self):
        """An approved agency should return an 200 response."""
        response = http_get_response(self.url, self.view, self.user, **self.kwargs)
        eq_(response.status_code, 200)

    @nose.tools.raises(Http404)
    def test_unapproved_not_found(self):
        """An unapproved agency should return a 404 response."""
        self.agency.status = 'pending'
        self.agency.save()
        http_get_response(self.url, self.view, self.user, **self.kwargs)

    def test_list(self):
        """The list should only contain approved agencies"""
        # pylint: disable=no-self-use
        approved_agency = factories.AgencyFactory()
        unapproved_agency = factories.AgencyFactory(status='pending')
        response = http_get_response(reverse('agency-list'), agency.views.AgencyList.as_view())
        agency_list = response.context_data['object_list']
        ok_(approved_agency in agency_list, 'Approved agencies should be listed.')
        ok_(unapproved_agency not in agency_list, 'Unapproved agencies should not be listed.')


class TestAgencyForm(TestCase):
    """Tests the AgencyForm"""

    def setUp(self):
        self.agency = factories.AgencyFactory()
        self.form = agency.forms.AgencyForm({'name': self.agency.name}, instance=self.agency)

    def test_validate_empty_form(self):
        """The form should have a name, at least"""
        # pylint: disable=no-self-use
        ok_(not agency.forms.AgencyForm().is_valid(),
            'Empty AgencyForm should not validate.')

    def test_instance_form(self):
        """The form should validate given only instance data"""
        ok_(self.form.is_valid())


class TestStaleAgency(TestCase):
    """Tests the stale agency task"""
    def setUp(self):
        self.stale_agency = factories.StaleAgencyFactory(stale=False)
        self.unstale_agency = factories.AgencyFactory(stale=True)
        self.task = StaleAgencyTaskFactory(agency=self.unstale_agency)

    def test_stale_task(self):
        """A stale agency should be marked as stale"""
        from muckrock.agency.tasks import stale
        stale()
        self.stale_agency.refresh_from_db()
        self.unstale_agency.refresh_from_db()
        self.task.refresh_from_db()
        ok_(self.stale_agency.stale, 'The stale agency should be marked as stale')
        ok_(not self.unstale_agency.stale, 'The unstale agency should be unmarked as stale.')
        ok_(self.task.resolved, 'The task for the unstale agency should be resolved automatically.')
