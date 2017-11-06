"""Forms for Agency application"""

from django import forms

from localflavor.us.forms import USPhoneNumberField

from muckrock.agency.models import (
        Agency,
        AgencyType,
        AgencyEmail,
        AgencyPhone,
        AgencyAddress,
        )
from muckrock.communication.models import (
        EmailAddress,
        PhoneNumber,
        Address,
        )
from muckrock.fields import FullEmailField
from muckrock.portal.models import (
        Portal,
        PORTAL_TYPES
        )


class AgencyForm(forms.ModelForm):
    """A form for an Agency"""

    email = FullEmailField(required=False)
    phone = USPhoneNumberField(required=False)
    fax = USPhoneNumberField(required=False)
    portal_url = forms.URLField(required=False)
    portal_type = forms.ChoiceField(
            choices=PORTAL_TYPES,
            initial='other',
            )

    def save(self, *args, **kwargs):
        """Save email, phone, fax, and address models on save"""
        agency = super(AgencyForm, self).save(*args, **kwargs)
        if self.cleaned_data['email']:
            email_address = EmailAddress.objects.fetch(self.cleaned_data['email'])
            AgencyEmail.objects.create(
                    agency=agency,
                    email=email_address,
                    request_type='primary',
                    email_type='to',
                    )
        if self.cleaned_data['phone']:
            phone_number, _ = PhoneNumber.objects.update_or_create(
                    number=self.cleaned_data['phone'],
                    defaults={'type': 'phone'},
                    )
            AgencyPhone.objects.create(
                    agency=agency,
                    phone=phone_number,
                    )
        if self.cleaned_data['fax']:
            fax_number, _ = PhoneNumber.objects.update_or_create(
                    number=self.cleaned_data['fax'],
                    defaults={'type': 'fax'},
                    )
            AgencyPhone.objects.create(
                    agency=agency,
                    phone=fax_number,
                    request_type='primary',
                    )
        if self.cleaned_data['address']:
            address, _ = Address.objects.get_or_create(
                    address=self.cleaned_data['address'],
                    )
            AgencyAddress.objects.create(
                    agency=agency,
                    address=address,
                    request_type='primary',
                    )
        if self.cleaned_data['portal_url']:
            portal, _ = Portal.objects.get_or_create(
                    url=self.cleaned_data['portal_url'],
                    defaults={
                        'type': self.cleaned_data['portal_type'],
                        'name': '%s %s' % (
                            agency,
                            dict(PORTAL_TYPES)[self.cleaned_data['portal_type']],
                            )
                        },
                    )
            agency.portal = portal
            agency.save()

    class Meta:
        # pylint: disable=too-few-public-methods
        model = Agency
        fields = [
                'name',
                'aliases',
                'address',
                'email',
                'url',
                'phone',
                'fax',
                'portal_url',
                'portal_type',
                ]
        labels = {
            'aliases': 'Alias',
            'url': 'Website',
            'address': 'Mailing Address'
        }
        help_texts = {
            'aliases': ('An alternate name for the agency, '
                        'e.g. "CIA" is an alias for "Central Intelligence Agency".')
        }


class CSVImportForm(forms.Form):
    """Import a CSV file of models"""
    csv_file = forms.FileField()
    type_ = forms.ModelChoiceField(queryset=AgencyType.objects.all(), required=False)
