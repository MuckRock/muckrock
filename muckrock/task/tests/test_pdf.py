"""
Tests for PDF generation
"""

# Django
from django.test import TestCase

# MuckRock
from muckrock.communication.models import MailCommunication
from muckrock.foia.factories import FOIACommunicationFactory
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
