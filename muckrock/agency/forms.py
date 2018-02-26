"""Forms for Agency application"""

# Django
from django import forms

# Third Party
from localflavor.us.forms import USZipCodeField
from localflavor.us.us_states import STATE_CHOICES
from phonenumber_field.formfields import PhoneNumberField

# MuckRock
from muckrock.agency.models import (
    Agency,
    AgencyAddress,
    AgencyEmail,
    AgencyPhone,
    AgencyType,
)
from muckrock.communication.models import Address, EmailAddress, PhoneNumber
from muckrock.fields import FullEmailField
from muckrock.portal.models import PORTAL_TYPES, Portal


class AgencyForm(forms.ModelForm):
    """A form for an Agency"""

    address_suite = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Suite / Building Number (Optional)'
            }
        ),
    )
    address_street = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Street'
        }),
    )
    address_city = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'City'
        }),
    )
    address_state = forms.ChoiceField(
        required=False,
        choices=(('', '---'),) + STATE_CHOICES,
    )
    address_zip = USZipCodeField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Zip'
        }),
    )
    email = FullEmailField(required=False)
    website = forms.URLField(label='General Website', required=False)
    phone = PhoneNumberField(required=False)
    fax = PhoneNumberField(required=False)
    portal_url = forms.URLField(
        required=False,
        help_text='This is a URL where you can submit a request directly from '
        'the website.  You should probably leave this blank unless you know '
        'this is what you want'
    )

    portal_type = forms.ChoiceField(
        choices=PORTAL_TYPES,
        initial='other',
    )

    def save(self, *args, **kwargs):
        """Save email, phone, fax, and address models on save"""
        agency = super(AgencyForm, self).save(*args, **kwargs)
        if self.cleaned_data['email']:
            email_address = EmailAddress.objects.fetch(
                self.cleaned_data['email']
            )
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
        if (
            self.cleaned_data['address_suite']
            or self.cleaned_data['address_street']
            or self.cleaned_data['address_city']
            or self.cleaned_data['address_state']
            or self.cleaned_data['address_zip']
        ):
            address, _ = Address.objects.get_or_create(
                suite=self.cleaned_data['address_suite'],
                street=self.cleaned_data['address_street'],
                city=self.cleaned_data['address_city'],
                state=self.cleaned_data['address_state'],
                zip_code=self.cleaned_data['address_zip'],
            )
            # clear out any previously set primary addresses
            AgencyAddress.objects.filter(
                agency=agency,
                request_type='primary',
            ).delete()
            AgencyAddress.objects.create(
                agency=agency,
                address=address,
                request_type='primary',
            )
        if self.cleaned_data['portal_url']:
            portal_type = self.cleaned_data['portal_type']
            portal, _ = Portal.objects.get_or_create(
                url=self.cleaned_data['portal_url'],
                defaults={
                    'type':
                        portal_type,
                    'name':
                        u'%s %s' % (
                            agency,
                            dict(PORTAL_TYPES)[portal_type],
                        )
                },
            )
            agency.portal = portal
            agency.save()

    def get_fields(self):
        """Get the fields for rendering"""
        field_order = [
            'name',
            'aliases',
            'address',
            'email',
            'url',
            'website',
            'phone',
            'fax',
            'portal_url',
            'portal_type',
        ]
        return [
            field if field == 'address' else self[field]
            for field in field_order
        ]

    class Meta:
        model = Agency
        fields = [
            'name',
            'aliases',
            'email',
            'url',
            'website',
            'phone',
            'fax',
            'portal_url',
            'portal_type',
        ]
        labels = {
            'aliases': 'Alias',
            'url': 'FOIA or public information contact page',
        }
        help_texts = {
            'aliases':
                'An alternate name for the agency, '
                'e.g. "CIA" is an alias for "Central Intelligence Agency".'
        }


class CSVImportForm(forms.Form):
    """Import a CSV file of models"""
    csv_file = forms.FileField()
    type_ = forms.ModelChoiceField(
        queryset=AgencyType.objects.all(), required=False
    )
