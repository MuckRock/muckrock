"""
Tests for fine uploader integration
"""

from django.core.urlresolvers import reverse
from django.test import TestCase, RequestFactory

from nose.tools import eq_, assert_false
import json

from muckrock.factories import (
        FOIACommunicationFactory,
        FOIAFileFactory,
        UserFactory,
        )
from muckrock.fine_uploader import views
from muckrock.foia.models import FOIAFile

# pylint: disable=no-self-use

class TestFineUploaderSuccessView(TestCase):
    """Tests for fine uploader success view"""

    def test_success_success(self):
        """Test a successful post to the success view"""
        comm = FOIACommunicationFactory()
        request_factory = RequestFactory()
        request = request_factory.post(
                reverse('fine-uploader-success'),
                {'comm_id': comm.pk, 'name': 'file_name', 'key': 'file_key'},
                )
        request.user = comm.foia.user
        response = views.success(request)
        eq_(response.status_code, 200)
        foia_file = FOIAFile.objects.get(comm=comm)
        eq_(foia_file.title, 'file_name')
        eq_(foia_file.ffile.name, 'file_key')

    def test_success_bad_comm(self):
        """Test a post to the success view with a non-existent communication"""
        request_factory = RequestFactory()
        request = request_factory.post(
                reverse('fine-uploader-success'),
                {'comm_id': 1234, 'name': 'file_name', 'key': 'file_key'},
                )
        request.user = UserFactory()
        response = views.success(request)
        eq_(response.status_code, 400)

    def test_success_bad_user(self):
        """Test a post to the success view with a bad user"""
        comm = FOIACommunicationFactory()
        request_factory = RequestFactory()
        request = request_factory.post(
                reverse('fine-uploader-success'),
                {'comm_id': comm.pk, 'name': 'file_name', 'key': 'file_key'},
                )
        request.user = UserFactory()
        response = views.success(request)
        eq_(response.status_code, 403)

    def test_success_bad_data(self):
        """Test a post to the success view with missing data"""
        comm = FOIACommunicationFactory()
        request_factory = RequestFactory()
        request = request_factory.post(
                reverse('fine-uploader-success'),
                {'comm_id': comm.pk},
                )
        request.user = comm.foia.user
        response = views.success(request)
        eq_(response.status_code, 400)


class TestFineUploaderSessionView(TestCase):
    """Tests for fine uploader session view"""

    def test_session_success(self):
        """Test a successful post to the session view"""
        comm = FOIACommunicationFactory()
        files = FOIAFileFactory.create_batch(3, comm=comm)
        FOIAFileFactory.create_batch(3)
        request_factory = RequestFactory()
        request = request_factory.get(
                reverse('fine-uploader-session'),
                {'comm_id': comm.pk},
                )
        request.user = comm.foia.user
        response = views.session(request)
        eq_(response.status_code, 200)
        file_data = json.loads(response.content)
        file_data.sort(key=lambda f: f['uuid'])
        files.sort(key=lambda f: f.pk)
        for file_datum, file_ in zip(file_data, files):
            eq_(file_datum['name'], file_.name())
            eq_(file_datum['uuid'], file_.pk)
            eq_(file_datum['size'], file_.ffile.size)
            eq_(file_datum['s3Key'], file_.ffile.name)

    def test_session_bad_comm(self):
        """Test a post to the session view with a non-existent communication"""
        request_factory = RequestFactory()
        request = request_factory.get(
                reverse('fine-uploader-session'),
                {'comm_id': 1234},
                )
        request.user = UserFactory()
        response = views.session(request)
        eq_(response.status_code, 400)

    def test_session_bad_user(self):
        """Test a post to the session view with a bad user"""
        comm = FOIACommunicationFactory()
        request_factory = RequestFactory()
        request = request_factory.get(
                reverse('fine-uploader-session'),
                {'comm_id': comm.pk, 'name': 'file_name', 'key': 'file_key'},
                )
        request.user = UserFactory()
        response = views.session(request)
        eq_(response.status_code, 403)


class TestFineUploaderDeleteView(TestCase):
    """Tests for fine uploader delete view"""

    def test_delete_success(self):
        """Test a successful post to the delete view"""
        file_ = FOIAFileFactory()
        request_factory = RequestFactory()
        request = request_factory.post(
                reverse('fine-uploader-delete'),
                {'key': file_.ffile.name},
                )
        request.user = file_.comm.foia.user
        response = views.delete(request)
        eq_(response.status_code, 200)
        assert_false(FOIAFile.objects.filter(pk=file_.pk).exists())

    def test_delete_bad_file(self):
        """Test a post to the delete view with a non-existent file"""
        request_factory = RequestFactory()
        request = request_factory.post(
                reverse('fine-uploader-delete'),
                {'key': 'foobar'},
                )
        request.user = UserFactory()
        response = views.delete(request)
        eq_(response.status_code, 400)

    def test_delete_bad_user(self):
        """Test a post to the delete view with a bad user"""
        file_ = FOIAFileFactory()
        request_factory = RequestFactory()
        request = request_factory.post(
                reverse('fine-uploader-success'),
                {'key': file_.ffile.name},
                )
        request.user = UserFactory()
        response = views.delete(request)
        eq_(response.status_code, 403)


class TestFineUploaderSignView(TestCase):
    """Tests for fine uploader delete view"""


class TestFineUploaderKeyView(TestCase):
    """Tests for fine uploader delete view"""


class TestFineUploaderBlankView(TestCase):
    """Tests for fine uploader blank view"""

    def test_blank(self):
        """Test the blank view"""
        request_factory = RequestFactory()
        request = request_factory.get(reverse('fine-uploader-blank'))
        request.user = UserFactory()
        response = views.blank(request)
        eq_(response.status_code, 200)
