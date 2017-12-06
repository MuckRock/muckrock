# -*- coding: utf-8 -*-
"""
PDF Class for Snail Mail PDF letter generation
"""

from django.conf import settings

from fpdf import FPDF

from datetime import date
from itertools import groupby
import os.path


class PDF(FPDF):
    """Shared PDF settings"""

    def footer(self):
        """Add page number to the footer"""
        self.set_y(-25)
        self.set_font('Times', 'I', 10)
        self.cell(0, 10, 'Page {} of {{nb}}'.format(self.page_no()), 0, 0, 'C')

    def configure(self):
        """Configure common settings"""
        self.add_font(
                'DejaVu',
                '',
                os.path.join(settings.FONT_PATH, 'DejaVuSerif.ttf'),
                uni=True,
                )
        self.alias_nb_pages()
        self.add_page()


class SnailMailPDF(PDF):
    """Custom PDF class for a snail mail task"""

    def __init__(self, comm, category):
        self.comm = comm
        self.appeal = category == 'a'
        super(SnailMailPDF, self).__init__('P', 'pt', 'Letter')

    def header(self):
        """Add letterhead"""
        self.set_font('DejaVu', '', 10)
        email = self.comm.foia.get_request_email()
        text = (
                'MuckRock News\n'
                'DEPT MR {pk}\n'
                '411A Highland Ave\n'
                'Somerville, MA 02144-2516\n'
                '{email}'.format(
                    pk=self.comm.foia.pk,
                    email=email,
                    ))
        width = self.get_string_width(email)
        self.set_xy(72 / 2, (72 * 3) / 4)
        self.multi_cell(width + 6, 13, text, 0, 'L')
        self.line(72 / 2, 1.7 * 72, 8 * 72, 1.7 * 72)
        self.ln(45)

    def generate(self):
        """Generate a PDF for a given FOIA"""
        # pylint: disable=invalid-name
        self.configure()
        self.rect(6.8 * 72, 10, 1.2 * 72, 72 / 4, 'F')
        self.dashed_line(0, 4 * 72, 72 / 4, 4 * 72, 2, 2)
        self.dashed_line(8.25 * 72, 4 * 72, 8.5 * 72, 4 * 72, 2, 2)
        if self.appeal:
            x = self.get_x()
            y = self.get_y()
            self.set_font('Arial', 'b', 18)
            self.set_xy(3.5 * 72, (72 * 3) / 4)
            law_name = self.comm.foia.jurisdiction.get_law_name(abbrev=True)
            self.cell(0, 0, u'{} APPEAL'.format(law_name))
            self.set_xy(x, y)
        self.set_font('DejaVu', '', 10)
        msg_body = self.comm.foia.render_msg_body(self.comm, appeal=self.appeal)
        self.multi_cell(0, 13, msg_body.rstrip(), 0, 'L')


class CoverPDF(PDF):
    """Custom PDF class for a cover page to bulk snail mail"""

    def __init__(self, info):
        self.info = info
        super(CoverPDF, self).__init__('P', 'pt', 'Letter')

    def header(self):
        """Add letterhead"""
        self.image(
                'muckrock/templates/lib/component/icon/logotype.png',
                72 / 2, 72 / 2, 3 * 72)
        self.line(72 / 2, 1.1 * 72, 8 * 72, 1.1 * 72)
        self.ln(70)

    def generate(self):
        """Generate a PDF cover page"""
        self.configure()
        self.set_font('DejaVu', '', 14)
        title = 'Bulk Snail Mail Cover Letter for {}'.format(
                date.today())
        self.cell(0, 0, title, 0, 1, 'C')
        self.ln(10)
        self.set_font('DejaVu', '', 10)
        lines = []
        grouped_info = groupby(
                self.info,
                lambda x: x[0].communication.foia.agency,
                )
        tab = u' ' * 8
        for agency, info in grouped_info:
            info = list(info)
            lines.append(u'\nAgency: {} - {} requests'.format(
                agency.name,
                len(info),
                ))
            for snail, pages, files in info:
                lines.append(u'\n{}□ MR #{} - "{}" by {} - {} pages'.format(
                    tab,
                    snail.communication.foia.pk,
                    snail.communication.foia.title,
                    snail.communication.from_user,
                    pages,
                    ))
                if snail.category == 'p':
                    lines.append(
                            u'{}□ Write a check for ${:.2f}'
                            .format(2 * tab, snail.amount))
                for file_, status in files:
                    if status == 'attached':
                        lines.append(
                                u'{}▣ Attached: {}'
                                .format(2 * tab, file_.name()))
                    elif status == 'skipped':
                        lines.append(
                                u'{}□ Print separately: {}'
                                .format(2 * tab, file_.name()))
                    else: # status == 'error'
                        lines.append(
                                u'{}□ Print separately (error): {}'
                                .format(2 * tab, file_.name()))
        text = u'\n'.join(lines)
        self.multi_cell(0, 13, text)
