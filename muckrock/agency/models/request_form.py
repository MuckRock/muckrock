"""
Agency Request form

Form filling in inspired by:
https://medium.com/@zwinny/filling-pdf-forms-in-python-the-right-way-eb9592e03dba
"""

# Django
from django.conf import settings
from django.db import models

# Standard Library
import inspect
from datetime import date
from io import BytesIO

# Third Party
from pdfrw import PageMerge, PdfReader, PdfWriter
from reportlab.pdfgen import canvas

# MuckRock
from muckrock.task.models import FlaggedTask


class AgencyRequestForm(models.Model):
    """A form an agency requires you to fill out in order to file a request"""

    name = models.CharField(max_length=255)
    form = models.FileField(upload_to="agency_forms/%Y/%m/%d", max_length=255)
    datetime_stamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def fill(self, comm):
        """Fill out the form - returns a bool indicating if manual review is needed"""
        if self.mappers.exists():
            data = self._get_data(comm)
            overlay = self._create_overlay(data)
            form = self._merge_overlay(overlay)
            name = "{}.pdf".format(self.name)
            comm.attach_file(content=form.read(), name=name, source="MuckRock")
            return False
        else:
            FlaggedTask.objects.create(
                foia=comm.foia,
                category="manual form",
                text="This request requires a form to be manually filled out before being "
                "sent.  Please fill it out, attach to the initial communication, and "
                "send it.\n\n{}".format(self.form.url),
            )
            return True

    def _get_data(self, comm):
        """Get the data for filling in the form"""
        return {m.field: getattr(self, m.value)(comm) for m in self.mappers.all()}

    def _create_overlay(self, data):
        """Create the filled in overlay"""
        # initiate an overlay buffer where we will fill in the information
        overlay_buffer = BytesIO()
        overlay_canvas = canvas.Canvas(overlay_buffer)
        overlay_canvas.setFont("Times-Roman", 10)
        # open a copy of the template form to fill in
        self.form.seek(0)
        template = PdfReader(self.form)
        # for each field on each page, find the position and fill in the information
        for page in template.Root.Pages.Kids:
            for field in page.Annots:
                sides_positions = [float(i) for i in field.Rect]
                left = min(sides_positions[0], sides_positions[2])
                bottom = min(sides_positions[1], sides_positions[3])
                label = field.T.decode() if field.T else None
                value = data.get(label, "")
                overlay_canvas.drawString(x=left + 2, y=bottom + 1, text=value)
            overlay_canvas.showPage()
        overlay_canvas.save()
        overlay_buffer.seek(0)
        return overlay_buffer

    def _merge_overlay(self, overlay):
        """Merge the overlay into the template"""
        # open a copy of the template form to merge in
        self.form.seek(0)
        template = PdfReader(self.form)
        # merge the overlay and template
        overlay_pdf = PdfReader(overlay)
        for t_page, o_page in zip(template.pages, overlay_pdf.pages):
            overlay = PageMerge().add(o_page)[0]
            PageMerge(t_page).add(overlay).render()
        final_form = BytesIO()
        PdfWriter().write(final_form, template)
        final_form.seek(0)
        return final_form

    # Form filling out data

    def _date(self, comm):
        """Today's date"""
        # pylint: disable=unused-argument
        return str(date.today())

    _date.value_choice = True

    def _is_email(self, comm):
        """Are we emailing this request?"""
        if comm.foia.email:
            return "x"
        else:
            return ""

    _is_email.value_choice = True

    def _is_fax(self, comm):
        """Are we faxing this request?"""
        if not comm.foia.email and comm.foia.fax:
            return "x"
        else:
            return ""

    _is_fax.value_choice = True

    def _is_snail(self, comm):
        """Are we snail mailing this request?"""
        if not comm.foia.email and not comm.foia.fax:
            return "x"
        else:
            return ""

    _is_snail.value_choice = True

    def _agency_name(self, comm):
        """Agency name"""
        return comm.foia.agency.name

    _agency_name.value_choice = True

    def _agency_address(self, comm):
        """Agency address"""
        address = comm.foia.agency.get_addresses("primary").first()
        address = address if address is not None else ""
        return str(address)

    _agency_address.value_choice = True

    def _requester_name(self, comm):
        """User's full name"""
        return comm.from_user.profile.full_name

    _requester_name.value_choice = True

    def _return_address_1(self, comm):
        """The street portion of the return address"""
        return f"{settings.ADDRESS_DEPT}, {settings.ADDRESS_STREET}".format(
            pk=comm.foia.pk
        )

    _return_address_1.value_choice = True

    def _return_address_2(self, comm):
        """City/State/Zip of the return address"""
        # pylint: disable=unused-argument
        return (
            f"{settings.ADDRESS_CITY}, {settings.ADDRESS_STATE} {settings.ADDRESS_ZIP}"
        )

    _return_address_2.value_choice = True

    def _phone(self, comm):
        """MuckRock's phone number"""
        # pylint: disable=unused-argument
        return settings.PHONE_NUMBER

    _phone.value_choice = True

    def _email(self, comm):
        """This request's email address"""
        return comm.foia.get_request_email()

    _email.value_choice = True


# grab all the value choices from the methods
# marked as being value choices and their docstrings
VALUE_CHOICES = [
    (m[0], m[1].__doc__)
    for m in inspect.getmembers(
        AgencyRequestForm(), predicate=lambda x: getattr(x, "value_choice", "")
    )
]


class AgencyRequestFormMapper(models.Model):
    """Map fields to values for an agency request form"""

    form = models.ForeignKey(
        "AgencyRequestForm", related_name="mappers", on_delete=models.CASCADE
    )
    field = models.CharField(max_length=255)
    value = models.CharField(max_length=255, choices=VALUE_CHOICES)

    def __str__(self):
        return "{} - {} - {}".format(self.form, self.field, self.value)
