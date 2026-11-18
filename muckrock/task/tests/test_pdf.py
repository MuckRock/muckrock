"""
Tests for PDF generation
"""

# Django
from django.core.files.base import ContentFile
from django.test import TestCase

# Standard Library
from io import BytesIO

# Third Party
from pypdf import PdfReader, PdfWriter

# MuckRock
from muckrock.communication.models import MailCommunication
from muckrock.foia.factories import FOIACommunicationFactory, FOIAFileFactory
from muckrock.task.factories import SnailMailTaskFactory
from muckrock.task.pdf import LobPDF, SnailMailPDF


class PDFTests(TestCase):
    """Test PDF generation"""

    def test_snail_mail_prepare(self):
        """Generate a SnailMailPDF"""
        snail = SnailMailTaskFactory()
        pdf = SnailMailPDF(
            snail.communication, snail.category, snail.switch, snail.amount
        )
        prepared_pdf, page_count, files, mail = pdf.prepare()
        assert prepared_pdf
        assert page_count == 1
        assert files == []
        assert isinstance(mail, MailCommunication)

    def test_lob_prepare(self):
        """Generate a LobPDF"""
        communication = FOIACommunicationFactory()
        pdf = LobPDF(communication, "n", False, 0)
        prepared_pdf, page_count, files, mail = pdf.prepare()
        assert prepared_pdf
        assert page_count == 1
        assert files == []
        assert isinstance(mail, MailCommunication)

    def test_truncates_an_over_limit_letter_with_a_matching_page_total(self):
        """A letter over the page limit is cut, and its footer counts the kept pages"""
        communication = FOIACommunicationFactory(
            communication="\n".join(f"Line {i}" for i in range(1200))
        )
        pdf = LobPDF(communication, "n", False, 0)
        prepared_pdf, _, _, _ = pdf.prepare()
        reader = PdfReader(prepared_pdf)
        assert len(reader.pages) == pdf.page_limit
        last_page = reader.pages[-1].extract_text()
        assert last_page.count(f"Page {pdf.page_limit} of {pdf.page_limit}") == 1

    def test_attaches_an_aes_encrypted_pdf_with_no_open_password(self):
        """An AES-encrypted attachment that opens without a password is merged"""
        source = PdfWriter()
        source.add_blank_page(width=612, height=792)
        source.add_blank_page(width=612, height=792)
        source.encrypt(user_password="", owner_password="owner", algorithm="AES-256")
        encrypted = BytesIO()
        source.write(encrypted)

        communication = FOIACommunicationFactory()
        attachment = FOIAFileFactory(
            comm=communication,
            ffile=ContentFile(encrypted.getvalue(), name="encrypted.pdf"),
        )
        pdf = LobPDF(communication, "n", False, 0)
        prepared_pdf, page_count, files, _ = pdf.prepare()

        assert files == [(attachment, "attached", 2)]
        assert page_count == 3
        assert len(PdfReader(prepared_pdf).pages) == 3
