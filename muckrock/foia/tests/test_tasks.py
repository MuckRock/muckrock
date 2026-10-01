# Django
from celery.exceptions import Retry
from django.conf import settings
from django.db import connection, reset_queries
from django.test import TestCase, override_settings

# Standard Library
from unittest.mock import MagicMock, patch

# Third Party
import boto3
from constance.test import override_config
from moto import mock_aws

# MuckRock
from muckrock.core.factories import UserFactory
from muckrock.foia.factories import FOIAFileFactory, FOIARequestFactory
from muckrock.foia.tasks import (
    ExportCsv,
    InvalidFileTypeError,
    classify_status,
    is_valid_file_type,
    upload_document_cloud,
)
from muckrock.task.factories import ResponseTaskFactory


class ExportCsvTests(TestCase):
    @mock_aws
    def test_db_calls(self):
        user = UserFactory()
        s3 = boto3.client("s3")
        s3.create_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)

        def get_num_queries(batch_size):
            foias = FOIARequestFactory.create_batch(batch_size)
            try:
                settings.DEBUG = True
                reset_queries()
                ExportCsv(user.pk, [f.pk for f in foias]).run()
                num_queries = len(connection.queries)
            finally:
                settings.DEBUG = False
                reset_queries()
            return num_queries

        assert get_num_queries(1) == get_num_queries(10)


@mock_aws
class IsValidFileTypeTests(TestCase):
    """Testing for valid file type logic"""

    def setUp(self):
        boto3.client("s3").create_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)

    def test_matching_pdf_is_valid(self):
        ffile = FOIAFileFactory(
            ffile__filename="doc.pdf", ffile__data=b"%PDF-1.7\nrest of file"
        )
        self.assertTrue(is_valid_file_type(ffile))

    def test_mismatched_content_is_invalid(self):
        # claims .pdf but the bytes are a PNG
        ffile = FOIAFileFactory(
            ffile__filename="doc.pdf", ffile__data=b"\x89PNG\r\n\x1a\n"
        )
        self.assertFalse(is_valid_file_type(ffile))


@mock_aws
@override_settings(DOCCLOUD_EXTENSIONS=[".pdf"])
class UploadDocumentCloudTests(TestCase):
    """upload_document_cloud rejects content/extension mismatches before it
    ever uploads. DOCCLOUD_EXTENSIONS is pinned so .pdf is a doccloud type and
    .mp3 is not"""

    def setUp(self):
        boto3.client("s3").create_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)

    @patch("muckrock.foia.tasks._upload_documentcloud")
    @patch("muckrock.foia.tasks.get_dc_client")
    def test_invalid_type_raises_and_does_not_upload(self, _mock_client, mock_upload):
        # .pdf extension, but PNG bytes -> mismatch
        ffile = FOIAFileFactory(
            ffile__filename="doc.pdf", ffile__data=b"\x89PNG\r\n\x1a\n"
        )
        with self.assertRaises(InvalidFileTypeError):
            upload_document_cloud(ffile.pk)
        mock_upload.assert_not_called()

    @patch("muckrock.foia.tasks._upload_documentcloud")
    @patch("muckrock.foia.tasks.get_dc_client")
    def test_valid_type_proceeds_to_upload(self, _mock_client, mock_upload):
        ffile = FOIAFileFactory(
            ffile__filename="doc.pdf", ffile__data=b"%PDF-1.7\nrest"
        )
        upload_document_cloud(ffile.pk)
        mock_upload.assert_called_once()

    @patch("muckrock.foia.tasks._upload_documentcloud")
    @patch("muckrock.foia.tasks.get_dc_client")
    def test_non_doccloud_skips_validation(self, _mock_client, mock_upload):
        # .mp3 is not in DOCCLOUD_EXTENSIONS -> is_doccloud() False -> no upload
        ffile = FOIAFileFactory(
            ffile__filename="notes.mp3", ffile__data=b"not audio at all"
        )
        upload_document_cloud(ffile.pk)
        mock_upload.assert_not_called()


def _doc(status, full_text="extracted body"):
    """Stand-in for a DocumentCloud Document exposing only what the loop reads."""
    doc = MagicMock()
    doc.status = status
    doc.full_text = full_text
    return doc


@override_settings(DOCCLOUD_EXTENSIONS=[".pdf"])
@override_config(ENABLE_GLOO=False)
class ClassifyStatusTests(TestCase):
    """Test for the classify status logic. Every file is a .pdf so is_doccloud()
    is true and the status branch under test actually fires."""

    @patch("muckrock.foia.tasks.get_document")
    def test_success_fetches_and_completes(self, mock_get_doc):
        mock_get_doc.return_value = _doc("success")
        task = ResponseTaskFactory()
        FOIAFileFactory(
            comm=task.communication, ffile__filename="doc.pdf", doc_id="123-slug"
        )

        classify_status(task.pk)

        mock_get_doc.assert_called_once_with("123-slug")

    @patch("muckrock.foia.tasks.get_document")
    def test_readable_also_uses_text(self, mock_get_doc):
        # "readable" is treated the same as success for text extraction
        mock_get_doc.return_value = _doc("readable")
        task = ResponseTaskFactory()
        FOIAFileFactory(
            comm=task.communication, ffile__filename="doc.pdf", doc_id="123-slug"
        )

        classify_status(task.pk)

        mock_get_doc.assert_called_once_with("123-slug")

    @patch("muckrock.foia.tasks.classify_status.retry", side_effect=Retry())
    @patch("muckrock.foia.tasks.get_document")
    def test_pending_triggers_retry(self, mock_get_doc, mock_retry):
        mock_get_doc.return_value = _doc("pending")
        task = ResponseTaskFactory()
        FOIAFileFactory(
            comm=task.communication, ffile__filename="doc.pdf", doc_id="123-slug"
        )

        with self.assertRaises(Retry):
            classify_status(task.pk)
        mock_retry.assert_called()

    @patch("muckrock.foia.tasks.classify_status.retry", side_effect=Retry())
    @patch("muckrock.foia.tasks.get_document")
    def test_terminal_status_classifies_without_retry(self, mock_get_doc, mock_retry):
        # error/nofile are terminal
        # just continue classification without that file
        for terminal in ("error", "nofile"):
            with self.subTest(status=terminal):
                mock_retry.reset_mock()
                mock_get_doc.return_value = _doc(terminal)
                task = ResponseTaskFactory()
                FOIAFileFactory(
                    comm=task.communication,
                    ffile__filename="doc.pdf",
                    doc_id="123-slug",
                )

                classify_status(task.pk)

                mock_retry.assert_not_called()

    @patch("muckrock.foia.tasks.classify_status.retry", side_effect=Retry())
    @patch("muckrock.foia.tasks.get_document")
    def test_doccloud_file_without_doc_id_retries(self, mock_get_doc, mock_retry):
        task = ResponseTaskFactory()
        FOIAFileFactory(comm=task.communication, ffile__filename="doc.pdf", doc_id="")

        with self.assertRaises(Retry):
            classify_status(task.pk)
        mock_get_doc.assert_not_called()
        mock_retry.assert_called()
