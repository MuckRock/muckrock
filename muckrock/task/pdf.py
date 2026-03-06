# -*- coding: utf-8 -*-
"""
PDF Class for Snail Mail PDF letter generation
"""

# Django
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone

# Standard Library
import logging
import os.path
import subprocess
from datetime import date
from io import BytesIO
from itertools import groupby
from tempfile import TemporaryDirectory

# Third Party
import emoji
import img2pdf
import pypdf
from fpdf import FPDF
from pypdf import PdfMerger, PdfReader
from pypdf.errors import PdfReadError

# MuckRock
from muckrock.communication.models import MailCommunication

# These are the dimensions of a standard sized PDF page
# in whatever units pypdf are using
PDF_WIDTH = 612
PDF_HEIGHT = 792

# adopted from: https://gist.github.com/tiarno/8a2995e70cee42f01e79

logger = logging.getLogger(__name__)


def walk(obj, fnt, emb):
    """
    If there is a key called 'BaseFont', that is a font that is used in the document.
    If there is a key called 'FontName' and another key in the same dictionary object
    that is called 'FontFilex' (where x is null, 2, or 3), then that fontname is
    embedded.

    We create and add to two sets, fnt = fonts used and emb = fonts embedded.
    """

    if isinstance(obj, pypdf.generic.IndirectObject):
        # recurse on indirect objects
        walk(obj.get_object(), fnt, emb)

    if not isinstance(obj, (pypdf.generic.DictionaryObject, pypdf.generic.ArrayObject)):
        # cannot check non dictionary or array objects for properties
        return

    fontkeys = set(["/FontFile", "/FontFile2", "/FontFile3"])
    if "/BaseFont" in obj:
        fnt.add(obj["/BaseFont"])
    if "/FontName" in obj:
        if [x for x in fontkeys if x in obj]:  # test to see if there is FontFile
            emb.add(obj["/FontName"])

    # recurse on dictionaries
    if isinstance(obj, pypdf.generic.DictionaryObject):
        for key in obj.keys():
            walk(obj[key], fnt, emb)

    # recurse on arrays
    elif isinstance(obj, pypdf.generic.ArrayObject):
        for i in obj:
            walk(i, fnt, emb)


def get_fonts(pdf):
    """Get all the fonts in the PDF and which are and are not embedded"""
    fonts = set()
    embedded = set()
    for page in pdf.pages:
        obj = page.get_object()
        walk(obj["/Resources"], fonts, embedded)

    unembedded = fonts - embedded
    return fonts, embedded, unembedded


# Fonts Lob allows to be unembedded
# https://docs.lob.com/#section/Standard-PDF-Fonts
ALLOWED_FONTS = [
    "Arial",
    "Arial,Bold",
    "Arial,BoldItalic",
    "Arial,Italic",
    "ArialMT",
    "Arial-BoldMT",
    "Arial-BoldItalicMT",
    "Arial-ItalicMT",
    "ArialNarrow",
    "ArialNarrow-Bold",
    "Calibri",
    "Calibri-Bold",
    "Calibri-Italic",
    "Courier",
    "Courier-Oblique",
    "Courier-Bold",
    "Courier-BoldOblique",
    "CourierNewPSMT",
    "CourierNewPS-ItalicMT",
    "CourierNewPS-BoldMT",
    "Helvetica",
    "Helvetica-Bold",
    "Helvetica-BoldOblique",
    "Helvetica-Oblique",
    "LucidaConsole",
    "MsSansSerif",
    "MsSansSerif,Bold",
    "Symbol",
    "Tahoma",
    "Tahoma-Bold",
    "Times-Bold",
    "Times-BoldItalic",
    "Times-Italic",
    "Times-Roman",
    "TimesNewRomanPS-BoldItalicMT",
    "TimesNewRomanPS-BoldMT",
    "TimesNewRomanPS-ItalicMT",
    "TimesNewRomanPSMT",
    "TimesNewRomanPSMT,Bold",
    "Verdana",
    "Verdana-Bold",
    "Verdana,Italic",
    "ZapfDingbats",
]


def needs_embedding(pdf):
    """We need to embed fonts if it contains a non-embedded font not in the list"""
    fonts, _embedded, _unembedded = get_fonts(pdf)
    return any(font.strip("/") not in ALLOWED_FONTS for font in fonts)


def handle_embedding(file):
    """Check if the file needs fonts embedded, and then embed them if it does"""
    pdf = PdfReader(file.ffile)
    if needs_embedding(pdf):
        with TemporaryDirectory() as tmp:
            input_path = os.path.join(tmp, "input.pdf")
            with open(input_path, "wb") as input_file:
                file.ffile.seek(0)
                input_file.write(file.ffile.read())
            output_path = os.path.join(tmp, "output.pdf")
            subprocess.run(
                "gs -q -dNOPAUSE -dBATCH -dPDFSETTINGS=/prepress -sDEVICE=pdfwrite "
                f"-sOutputFile={output_path} {input_path}".split(),
                check=True,
            )
            with open(output_path, "rb") as output_file:
                file.ffile.save(file.name(), ContentFile(output_file.read()))


class PDF(FPDF):
    """Shared PDF settings"""

    def footer(self):
        """Add page number to the footer"""
        self.set_y(-25)
        self.set_font("Times", "I", 10)
        self.cell(0, 10, "Page {} of {{nb}}".format(self.page_no()), 0, 0, "C")

    def configure(self):
        """Configure common settings"""
        self.add_font(
            "DejaVu", "", os.path.join(settings.FONT_PATH, "DejaVuSerif.ttf"), uni=True
        )
        self.alias_nb_pages()
        self.add_page()


class MailPDF(PDF):
    """Base class for other mail classes to inherit from"""

    def __init__(self, comm, category, switch, amount=None):
        self.comm = comm
        self.appeal = category == "a"
        self.switch = switch
        self.amount = amount
        if amount:
            self.page_limit = 6
        else:
            self.page_limit = 12
        super().__init__("P", "pt", "Letter")

    def header(self):
        """Add letterhead"""
        self.set_font("DejaVu", "", 10)
        email = self.comm.foia.get_request_email()
        text = (
            f"{settings.ADDRESS_NAME}\n"
            f"{settings.ADDRESS_DEPT}\n"
            f"{settings.ADDRESS_STREET}\n"
            f"{settings.ADDRESS_CITY}, {settings.ADDRESS_STATE} "
            f"{settings.ADDRESS_ZIP}\n"
            f"{email}".format(pk=self.comm.foia.pk)
        )
        width = self.get_string_width(email)
        self.set_xy(72 / 2, (72 * 0.6))
        self.multi_cell(width + 6, 13, text, 0, "L")
        self.line(72 / 2, 1.55 * 72, 8 * 72, 1.55 * 72)
        self.ln(38)

    def generate(self, num_msgs=5):
        """Generate a PDF for a given FOIA"""
        self.configure()
        self._extra_generate()
        if self.appeal:
            law_name = self.comm.foia.jurisdiction.get_law_name(abbrev=True)
            self._extra_header("{} APPEAL".format(law_name))
        self.set_font("DejaVu", "", 10)
        msg_body = self.comm.foia.render_msg_body(
            self.comm,
            appeal=self.appeal,
            switch=self.switch,
            include_address=self.include_address,
            payment=self.amount is not None and self.amount > 0,
            num_msgs=num_msgs,
        )
        # remove emoji's, as they break pdf rendering
        msg_body = emoji.get_emoji_regexp().sub("", msg_body)
        self.multi_cell(0, 13, msg_body.rstrip(), 0, "L")

    def _extra_header(self, text):
        """Add an extra line to the header"""
        x = self.get_x()
        y = self.get_y()
        self.set_font("Arial", "b", 18)
        self.set_xy(3.5 * 72, (72 * 3) / 4)
        self.cell(0, 0, text)
        self.set_xy(x, y)

    def _extra_generate(self):
        """Hook for subclasses to override"""

    def _resize_pages(self, pages):
        """Resize the page if necessary and able"""
        i = 0
        for page in pages:
            i += 1
            rotated = False
            width = page.pagedata.mediabox.width
            height = page.pagedata.mediabox.height
            # account for rotations
            rotation = page.pagedata.rotation
            if rotation is not None and rotation % 180 == 90:
                width, height = height, width
                rotated = not rotated
            if width > height:
                page.pagedata.rotate(-90)
                # page.transfer_rotation_to_content()
                width, height = height, width
                rotated = not rotated
            if (width, height) != (PDF_WIDTH, PDF_HEIGHT):
                if rotated:
                    page.pagedata.scale_to(PDF_HEIGHT, PDF_WIDTH)
                else:
                    page.pagedata.scale_to(PDF_WIDTH, PDF_HEIGHT)

    def _handle_file(self, file_, files, merger):
        """Determine if we can attach the file"""
        img_exts = ["jpg", "jpeg", "png"]
        total_pages = self.page

        if file_.get_extension() in img_exts:
            mem_file = BytesIO(img2pdf.convert(file_.ffile))
            if total_pages + 1 > self.page_limit:
                # too long, skip
                files.append((file_, "skipped", 1))
            else:
                merger.append(mem_file)
                files.append((file_, "attached", 1))
                total_pages += 1
        elif file_.get_extension() == "pdf":
            try:
                # detect un-embedded fonts
                handle_embedding(file_)
                pages = len(PdfReader(file_.ffile).pages)
                if pages + total_pages > self.page_limit:
                    # too long, skip
                    files.append((file_, "skipped", pages))
                else:
                    merger.append(file_.ffile)
                    files.append((file_, "attached", pages))
                    total_pages += pages
            except (PdfReadError, ValueError, subprocess.CalledProcessError):
                files.append((file_, "error", 0))
        else:
            files.append((file_, "skipped", 0))

        return total_pages

    def prepare(self, address_override=None, num_msgs=5):
        """Prepare the PDF to be sent by appending attachments"""
        # generate the pdf and merge all pdf attachments
        # keep track of any problematic attachments
        self.generate(num_msgs)
        total_pages = self.page
        logger.info("prepare num_msgs %s total_pages %s", num_msgs, total_pages)

        payment = self.amount is not None and self.amount > 0
        if payment and num_msgs > 1:
            # never send more than 1 extra message with payments
            num_msgs = 1
        if total_pages > self.page_limit and num_msgs > 0:
            # If we are over the page limit before adding any attachments,
            # try rendering with less extra messages

            # We need a new FPDF object since there is no easy way to undo writing
            # to the PDF
            new_pdf = type(self)(
                self.comm, "a" if self.appeal else "", self.switch, self.amount
            )
            if num_msgs > 1:
                num_msgs = 1
            else:
                num_msgs = 0
            return new_pdf.prepare(address_override, num_msgs=num_msgs)

        self.page = min(self.page, self.page_limit)
        merger = PdfMerger(strict=False)
        merger.append(BytesIO(self.output(dest="S").encode("latin-1")))
        files = []
        for file_ in self.comm.files.all():
            total_pages = self._handle_file(file_, files, merger)

        single_pdf = BytesIO()
        try:
            self._resize_pages(merger.pages)
            merger.write(single_pdf)
        except (PdfReadError, TypeError):
            return (None, None, files, None)

        # create the mail communication object
        address = address_override if address_override else self.comm.foia.address
        mail, _ = MailCommunication.objects.update_or_create(
            communication=self.comm,
            defaults={"to_address": address, "sent_datetime": timezone.now()},
        )
        single_pdf.seek(0)
        mail.pdf.save("{}.pdf".format(self.comm.pk), ContentFile(single_pdf.read()))

        # return to begining of merged pdf before returning
        single_pdf.seek(0)

        return (single_pdf, total_pages, files, mail)


class SnailMailPDF(MailPDF):
    """Custom PDF class for a snail mail task"""

    include_address = True

    def _extra_generate(self):
        """Add snail mail only features to PDF"""
        # Add shapes to assist staff in dealing with printed letters
        # New letter rectangle
        self.rect(6.8 * 72, 10, 1.2 * 72, 72 / 4, "F")
        # Fold lines
        self.dashed_line(0, 4 * 72, 72 / 4, 4 * 72, 2, 2)
        self.dashed_line(8.25 * 72, 4 * 72, 8.5 * 72, 4 * 72, 2, 2)

        # Check notification
        if self.amount:
            self._extra_header("Check Enclosed for ${:.2f}".format(self.amount))


class LobPDF(MailPDF):
    """Custom PDF class for mailing through Lob"""

    include_address = False

    def header(self):
        """Add letterhead"""
        if self.page_no() > 1:
            super().header()

    def _extra_generate(self):
        """Add Lob only features to PDF"""
        # whitespace for lob to insert address
        self.set_xy(72 * 0.4, (72 * 2.6))


class CoverPDF(PDF):
    """Custom PDF class for a cover page to bulk snail mail"""

    def __init__(self, info):
        self.info = info
        super().__init__("P", "pt", "Letter")

    def header(self):
        """Add letterhead"""
        self.image(
            "muckrock/templates/lib/component/icon/logotype.png", 72 / 2, 72 / 2, 3 * 72
        )
        self.line(72 / 2, 1.1 * 72, 8 * 72, 1.1 * 72)
        self.ln(70)

    def generate(self):
        """Generate a PDF cover page"""
        self.configure()
        self.set_font("DejaVu", "", 14)
        title = "Bulk Snail Mail Cover Letter for {}".format(date.today())
        self.cell(0, 0, title, 0, 1, "C")
        self.ln(10)
        self.set_font("DejaVu", "", 10)
        lines = []
        grouped_info = groupby(self.info, lambda x: x[0].communication.foia.agency)
        tab = " " * 8
        for agency, info in grouped_info:
            info = list(info)
            lines.append("\nAgency: {} - {} requests".format(agency.name, len(info)))
            for snail, pages, files in info:
                if pages is None:
                    lines.append(
                        '\n{}□ Error: MR #{} - "{}" by {}'.format(
                            tab,
                            snail.communication.foia.pk,
                            snail.communication.foia.title,
                            snail.communication.from_user,
                        )
                    )
                else:
                    if snail.communication.foia.address:
                        warning = ""
                    else:
                        warning = "Warning - No Address: "
                    lines.append(
                        '\n{}□ {}MR #{} - "{}" by {} - {} pages'.format(
                            tab,
                            warning,
                            snail.communication.foia.pk,
                            snail.communication.foia.title,
                            snail.communication.from_user,
                            pages,
                        )
                    )
                if snail.category == "p":
                    lines.append(
                        "{}□ Write a {}check for ${:.2f}".format(
                            2 * tab,
                            (
                                "CERTIFIED "
                                if snail.amount >= settings.CHECK_LIMIT
                                else ""
                            ),
                            snail.amount,
                        )
                    )
                for file_, status, pages_ in files:
                    if status == "attached":
                        lines.append(
                            "{}▣ Attached: {} - {} pages".format(
                                2 * tab, file_.name(), pages_
                            )
                        )
                    elif status == "skipped":
                        lines.append(
                            "{}□ Print separately: {}".format(2 * tab, file_.name())
                        )
                    else:  # status == 'error'
                        lines.append(
                            "{}□ Print separately (error): {}".format(
                                2 * tab, file_.name()
                            )
                        )
        text = "\n".join(lines)
        self.multi_cell(0, 13, text, 0, "L")
