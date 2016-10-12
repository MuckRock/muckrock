"""
Tests for FOIA Machine models.
"""

from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.loader import render_to_string
from django.test import TestCase
from django.utils import timezone

from datetime import timedelta
from django_hosts.resolvers import reverse
from nose.tools import eq_, ok_, raises

from muckrock.factories import UserFactory, AgencyFactory
from muckrock.foiamachine import factories, models

class TestFoiaMachineRequest(TestCase):
    """The FOIA Machine Request should store information we need to send a request."""
    def setUp(self):
        self.user = UserFactory()
        self.title = 'Test Request'
        self.request_language = 'Lorem ipsum'
        self.agency = AgencyFactory()
        self.jurisdiction = self.agency.jurisdiction
        self.foi = factories.FoiaMachineRequestFactory(
            user=self.user,
            title=self.title,
            request_language=self.request_language,
            jurisdiction=self.jurisdiction,
        )

    def test_create(self):
        """Requests should only require a user, a title,
        request language, and a jurisdiction to be created."""
        foi = models.FoiaMachineRequest.objects.create(
            user=self.user,
            title=self.title,
            request_language=self.request_language,
            jurisdiction=self.jurisdiction,
        )
        ok_(foi, 'The request should be created.')
        ok_(foi.slug, 'The slug should be created automatically.')

    def test_unicode(self):
        """Requests should use their titles when converted to unicode."""
        eq_(unicode(self.foi), self.foi.title,
            'The Unicode representation should be the title.')

    def test_get_absolute_url(self):
        """Request urls should include their slug and their id."""
        kwargs = {
            'slug': self.foi.slug,
            'pk': self.foi.pk,
        }
        actual_url = self.foi.get_absolute_url()
        expected_url = reverse('foi-detail', host='foiamachine', kwargs=kwargs)
        eq_(actual_url, expected_url)

    def test_generate_letter(self):
        """Using default information, the request should be able to generate a letter."""
        template = 'text/foia/request.txt'
        context = {
            'jurisdiction': self.foi.jurisdiction,
            'document_request': self.foi.request_language,
            'user_name': self.foi.user.get_full_name()
        }
        expected_letter = render_to_string(template, context=context).strip()
        actual_letter = self.foi.generate_letter()
        eq_(actual_letter, expected_letter)

    def test_generate_sharing_code(self):
        """The request should be able to generate a code for privately sharing urls."""
        ok_(self.foi.generate_sharing_code())

    def test_date_submitted(self):
        """The date submitted should be the first communication date or None."""
        comm = factories.FoiaMachineCommunicationFactory(request=self.foi)
        eq_(self.foi.date_submitted, comm.date.date())

    def test_date_due(self):
        """The date due should be the date submitted plus the jurisdiction's response time."""
        comm = factories.FoiaMachineCommunicationFactory(request=self.foi)
        expected_date_due = comm.date.date() + timedelta(self.foi.jurisdiction.get_days())
        eq_(self.foi.date_due, expected_date_due)

    @raises(AttributeError)
    def test_date_submitted_no_comms(self):
        """A request with no sent communications should raise an error."""
        self.foi.date_submitted

    @raises(AttributeError)
    def test_date_due_no_comms(self):
        """A request with no sent communications should raise an error."""
        self.foi.date_due

    def test_days_until_due(self):
        """The days until due should compare the date due to today's date."""
        comm = factories.FoiaMachineCommunicationFactory(request=self.foi)
        eq_(self.foi.days_until_due, (self.foi.date_due - timezone.now().date()).days)
        # If there is no communication, the default should be 0
        comm.delete()
        eq_(self.foi.days_until_due, 0)

    def test_is_overdue(self):
        """The request should be overdue if days_until_due is negative."""
        overdue_date = timezone.now().date() - timedelta(self.foi.jurisdiction.get_days() + 10)
        comm = factories.FoiaMachineCommunicationFactory(request=self.foi, date=overdue_date)
        ok_(self.foi.is_overdue)
        # Now let's make it not overdue
        comm.date = timezone.now().date()
        comm.save()
        ok_(not self.foi.is_overdue)

    def test_days_overdue(self):
        """Days overdue should just be the inverse of days_until_due."""
        overdue_date = timezone.now().date() - timedelta(self.foi.jurisdiction.get_days() + 10)
        comm = factories.FoiaMachineCommunicationFactory(request=self.foi, date=overdue_date)
        eq_(self.foi.days_overdue, self.foi.days_until_due * -1)


class TestFoiaMachineCommunication(TestCase):
    """The FOIA Machine Communication should store information
    about communications between users and agencies."""
    def setUp(self):
        self.foi = factories.FoiaMachineRequestFactory()
        self.comm = factories.FoiaMachineCommunicationFactory(request=self.foi)

    def test_create(self):
        """A request, sender, and message should be required to create a request."""
        comm = models.FoiaMachineCommunication(
            request=self.foi,
            sender=unicode(self.foi.user),
            message='Lorem ipsum dolor su amit.'
        )
        ok_(comm)

    def test_unicode(self):
        """The string representation of a communication includes sender and receiver info."""
        eq_(unicode(self.comm),
            'Communication from %s to %s' % (self.comm.sender, self.comm.receiver))


class TestFoiaMachineFile(TestCase):
    """The FOIA Machine File should attach files to communications."""
    def setUp(self):
        self.comm = factories.FoiaMachineCommunicationFactory()
        self.file = factories.FoiaMachineFileFactory(communication=self.comm)

    def test_create(self):
        """A communication, a file, and a filename should be required to create a new file."""
        file = models.FoiaMachineFile(
            communication=self.comm,
            file=SimpleUploadedFile('filename.txt', 'Test file contents'),
            name='filename.txt')
        ok_(file)

    def test_unicode(self):
        """The string representation of a file should be its name."""
        eq_(unicode(self.file), u'%s' % self.file.name)
