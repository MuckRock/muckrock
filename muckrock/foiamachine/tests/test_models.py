"""
Tests for FOIA Machine models.
"""

# Django
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.loader import render_to_string
from django.test import TestCase
from django.utils import timezone

# Standard Library
from datetime import timedelta

# Third Party
import pytest
from django_hosts.resolvers import reverse

# MuckRock
from muckrock.core.factories import AgencyFactory, UserFactory
from muckrock.foiamachine import factories, models


class TestFoiaMachineRequest(TestCase):
    """The FOIA Machine Request should store information we need to send a request."""

    def setUp(self):
        self.user = UserFactory()
        self.title = "Test Request"
        self.request_language = "Lorem ipsum"
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
        assert foi, "The request should be created."
        assert foi.slug, "The slug should be created automatically."

    def test_unicode(self):
        """Requests should use their titles when converted to unicode."""
        assert (
            str(self.foi) == self.foi.title
        ), "The Unicode representation should be the title."

    def test_get_absolute_url(self):
        """Request urls should include their slug and their id."""
        kwargs = {"slug": self.foi.slug, "pk": self.foi.pk}
        actual_url = self.foi.get_absolute_url()
        expected_url = reverse("foi-detail", host="foiamachine", kwargs=kwargs)
        assert actual_url == expected_url

    def test_generate_letter(self):
        """Using default information, the request should be able to generate a
        letter."""
        template = "text/foia/request.txt"
        context = {
            "jurisdiction": self.foi.jurisdiction,
            "document_request": self.foi.request_language,
            "user_name": self.foi.user.profile.full_name,
        }
        expected_letter = render_to_string(template, context=context).strip()
        actual_letter = self.foi.generate_letter()
        assert actual_letter == expected_letter

    def test_generate_sharing_code(self):
        """The request should be able to generate a code for privately sharing urls."""
        assert self.foi.generate_sharing_code()

    def test_date_submitted(self):
        """The date submitted should be the first communication date or None."""
        comm = factories.FoiaMachineCommunicationFactory(request=self.foi)
        assert self.foi.date_submitted == comm.date

    def test_date_due(self):
        """The date due should be the date submitted plus the jurisdiction's
        response time."""
        comm = factories.FoiaMachineCommunicationFactory(request=self.foi)
        expected_date_due = comm.date + timedelta(self.foi.jurisdiction.days)
        assert self.foi.date_due == expected_date_due

    def test_date_submitted_no_comms(self):
        """A request with no sent communications should raise an error."""
        # pylint: disable=pointless-statement
        with pytest.raises(AttributeError):
            self.foi.date_submitted

    def test_date_due_no_comms(self):
        """A request with no sent communications should raise an error."""
        # pylint: disable=pointless-statement
        with pytest.raises(AttributeError):
            self.foi.date_due

    def test_days_until_due(self):
        """The days until due should compare the date due to today's date."""
        comm = factories.FoiaMachineCommunicationFactory(request=self.foi)
        assert self.foi.days_until_due == (self.foi.date_due - timezone.now()).days
        # If there is no communication, the default should be 0
        comm.delete()
        assert self.foi.days_until_due == 0

    def test_is_overdue(self):
        """The request should be overdue if days_until_due is negative."""
        overdue_date = timezone.now() - timedelta(self.foi.jurisdiction.days + 10)
        comm = factories.FoiaMachineCommunicationFactory(
            request=self.foi, date=overdue_date
        )
        assert self.foi.is_overdue
        # Now let's make it not overdue
        comm.date = timezone.now()
        comm.save()
        assert not self.foi.is_overdue

    def test_days_overdue(self):
        """Days overdue should just be the inverse of days_until_due."""
        overdue_date = timezone.now() - timedelta(self.foi.jurisdiction.days + 10)
        factories.FoiaMachineCommunicationFactory(request=self.foi, date=overdue_date)
        assert self.foi.days_overdue == self.foi.days_until_due * -1


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
            sender=str(self.foi.user),
            message="Lorem ipsum dolor su amit.",
        )
        assert comm

    def test_unicode(self):
        """The string representation of a communication includes sender and
        receiver info."""
        assert str(self.comm) == "Communication from %s to %s" % (
            self.comm.sender,
            self.comm.receiver,
        )


class TestFoiaMachineFile(TestCase):
    """The FOIA Machine File should attach files to communications."""

    def setUp(self):
        self.comm = factories.FoiaMachineCommunicationFactory()
        self.file = factories.FoiaMachineFileFactory(communication=self.comm)

    def test_create(self):
        """A communication, a file, and a filename should be required to create
        a new file."""
        _file = models.FoiaMachineFile(
            communication=self.comm,
            file=SimpleUploadedFile("filename.txt", b"Test file contents"),
            name="filename.txt",
        )
        assert _file

    def test_unicode(self):
        """The string representation of a file should be its name."""
        assert str(self.file) == "%s" % self.file.name
