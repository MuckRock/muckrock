"""
FOIA forms for dealing with communications
"""

# Django
from django import forms
from django.contrib.auth.models import User

# Third Party
import phonenumbers
from autocomplete_light import shortcuts as autocomplete_light
from phonenumber_field.formfields import PhoneNumberField

# MuckRock
from muckrock.communication.models import EmailAddress, PhoneNumber
from muckrock.fields import EmptyLastModelChoiceField
from muckrock.foia.models import FOIACommunication
from muckrock.forms import TaggitWidget

AGENCY_STATUS = [
    ('processed', 'Further Response Coming'),
    ('fix', 'Fix Required'),
    ('payment', 'Payment Required'),
    ('rejected', 'Rejected'),
    ('no_docs', 'No Responsive Documents'),
    ('done', 'Completed'),
    ('partial', 'Partially Completed'),
]


class FOIAAgencyReplyForm(forms.Form):
    """Form for direct agency reply"""
    status = forms.ChoiceField(
        label="What's the current status of the request?",
        choices=AGENCY_STATUS,
        help_text=' ',
    )
    tracking_id = forms.CharField(
        label='Tracking Number',
        help_text="If your agency assign a tracking number to the request, "
        "please enter it here.  We'll include this number in future "
        "followups if necessary",
        required=False,
    )
    date_estimate = forms.DateField(
        label='Estimated Completion Date',
        help_text='Enter the date you expect the request to be fufilled by.  '
        'We will not follow up with you until this date.',
        required=False,
    )
    price = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'class': 'currency-field'
        }),
        required=False,
    )
    reply = forms.CharField(
        label='Message to the requester',
        widget=forms.Textarea(),
    )

    def clean(self):
        """Make price required if status is set to payment"""
        cleaned_data = super(FOIAAgencyReplyForm, self).clean()
        status = cleaned_data.get('status')
        price = cleaned_data.get('price')

        if status == 'payment' and price is None:
            self.add_error(
                'price',
                'You must set a price when setting the '
                'status to payment required',
            )
        return cleaned_data


class SendViaForm(forms.Form):
    """Form logic for specifying an address type to send to
    Shoul dbe subclassed"""

    via = forms.ChoiceField(
        choices=(
            ('portal', 'Portal'),
            ('email', 'Email'),
            ('fax', 'Fax'),
            ('snail', 'Snail Mail'),
        ),
    )
    email = autocomplete_light.ModelChoiceField(
        'EmailAddressAutocomplete',
        queryset=EmailAddress.objects.filter(status='good'),
        required=False,
    )
    fax = autocomplete_light.ModelChoiceField(
        'FaxAutocomplete',
        queryset=PhoneNumber.objects.filter(status='good', type='fax'),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        initial = kwargs.pop('initial', {})
        contact_info = kwargs.pop('contact_info', {})
        for addr in ('portal', 'email', 'fax'):
            if (
                contact_info.get(addr)
                or (self.foia and getattr(self.foia, addr))
            ):
                via = addr
                break
        else:
            via = 'snail'
        initial.update({
            'via':
                via,
            'email':
                contact_info.get('email') or (self.foia and self.foia.email),
            'fax':
                contact_info.get('fax') or (self.foia and self.foia.fax),
        })
        super(SendViaForm, self).__init__(*args, initial=initial, **kwargs)
        # create auto complete fields for creating new instances
        # these are created here since they have invalid identifier names
        # only add them if the field is bound, as we do not want to add them
        # to the form display, but do want to use them to process incoming data
        if self.is_bound:
            self.fields['email-autocomplete'] = forms.CharField(
                widget=forms.HiddenInput(),
                required=False,
            )
            self.fields['fax-autocomplete'] = forms.CharField(
                widget=forms.HiddenInput(),
                required=False,
            )
        # remove portal choice if the agency does not use a portal
        if self.foia and self.foia.agency and not self.foia.agency.portal:
            self.fields['via'].choices = (
                ('email', 'Email'),
                ('fax', 'Fax'),
                ('snail', 'Snail Mail'),
            )

    def clean(self):
        """Ensure the selected method is ok for this foia and the correct
        corresponding information is provided"""

        cleaned_data = super(SendViaForm, self).clean()
        if cleaned_data.get('via') == 'email' and not cleaned_data['email']:
            self._clean_email(cleaned_data)
        elif cleaned_data.get('via') == 'fax' and not cleaned_data['fax']:
            self._clean_fax(cleaned_data)
        return cleaned_data

    def _clean_email(self, cleaned_data):
        """Attempt to clean the email during full form clean"""
        if cleaned_data['email-autocomplete']:
            email = EmailAddress.objects.fetch(
                cleaned_data['email-autocomplete']
            )
            if email:
                cleaned_data['email'] = email
            else:
                self.add_error(
                    'email',
                    'Invalid email address',
                )
        else:
            self.add_error(
                'email',
                'An email address is required if resending via email',
            )

    def _clean_fax(self, cleaned_data):
        """Attempt to clean the fax during full form clean"""
        if cleaned_data['fax-autocomplete']:
            try:
                number = phonenumbers.parse(
                    cleaned_data['fax-autocomplete'], 'US'
                )
            except phonenumbers.NumberParseException:
                self.add_error(
                    'fax',
                    'Invalid fax number',
                )
            else:
                if phonenumbers.is_valid_number(number):
                    phone, _ = PhoneNumber.objects.update_or_create(
                        number=number,
                        defaults={'type': 'fax'},
                    )
                    cleaned_data['fax'] = phone
                else:
                    self.add_error(
                        'fax',
                        'Invalid fax number',
                    )
        else:
            self.add_error(
                'fax',
                'A fax number is required if resending via fax',
            )


class FOIAAdminFixForm(SendViaForm):
    """Form with extra options for staff to follow up to requests"""

    from_user = forms.ModelChoiceField(
        label='From',
        queryset=User.objects.none(),
    )
    other_emails = forms.CharField(
        label='CC',
        required=False,
        help_text='Comma seperated',
        widget=TaggitWidget('EmailAddressAutocomplete'),
    )
    subject = forms.CharField(max_length=255)
    comm = forms.CharField(label='Body', widget=forms.Textarea())

    field_order = [
        'from_user',
        'via',
        'email',
        'other_emails',
        'fax',
        'subject',
        'comm',
    ]

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request')
        self.foia = kwargs.pop('foia')
        super(FOIAAdminFixForm, self).__init__(*args, **kwargs)
        muckrock_staff = User.objects.get(username='MuckrockStaff')
        self.fields['from_user'].queryset = User.objects.filter(
            pk__in=[
                muckrock_staff.pk,
                request.user.pk,
                self.foia.user.pk,
            ]
        )
        self.fields['from_user'].initial = request.user.pk

    def clean_other_emails(self):
        """Validate the other_emails field"""
        return EmailAddress.objects.fetch_many(
            self.cleaned_data['other_emails'],
            ignore_errors=False,
        )


class ResendForm(SendViaForm):
    """A form for resending a communication"""
    communication = forms.ModelChoiceField(
        queryset=FOIACommunication.objects.all(),
        widget=forms.HiddenInput(),
    )

    def __init__(self, *args, **kwargs):
        # set initial data based on the communication
        comm = kwargs.pop('communication', None)
        if comm:
            self.foia = comm.foia
        else:
            self.foia = None
        initial = kwargs.pop('initial', {})
        initial.update({'communication': comm})
        super(ResendForm, self).__init__(*args, initial=initial, **kwargs)

    def clean(self):
        """Set self.foia during cleaning"""
        self.foia = self.cleaned_data['communication'].foia
        return super(ResendForm, self).clean()


class ContactInfoForm(SendViaForm):
    """A form to let advanced users control where the communication will be sent"""

    email = EmptyLastModelChoiceField(
        queryset=EmailAddress.objects.none(),
        required=False,
        empty_label='Other...',
    )
    other_email = forms.EmailField(required=False)
    fax = EmptyLastModelChoiceField(
        queryset=PhoneNumber.objects.none(),
        required=False,
        empty_label='Other...',
    )
    other_fax = PhoneNumberField(required=False)

    def __init__(self, *args, **kwargs):
        self.foia = kwargs.pop('foia')
        super(ContactInfoForm, self).__init__(*args, **kwargs)
        self.fields['email'].queryset = self.foia.agency.emails.filter(
            status='good',
        ).exclude(
            email__endswith='muckrock.com',
        ).distinct()
        self.fields['fax'].queryset = self.foia.agency.phones.filter(
            status='good',
            type='fax',
        ).distinct()

    def clean(self):
        """Make other fields required if chosen"""
        cleaned_data = super(ContactInfoForm, self).clean()
        if (
            cleaned_data.get('via') == 'email'
            and not cleaned_data.get('email')
            and not cleaned_data.get('other_email')
        ):
            self.add_error(
                'other_email',
                'Please enter an email address',
            )
        if (
            cleaned_data.get('via') == 'fax' and not cleaned_data.get('fax')
            and not cleaned_data.get('other_fax')
        ):
            self.add_error(
                'other_fax',
                'Please enter a fax number',
            )
        return cleaned_data

    def clean_other_email(self):
        """Turn other email into an Email Address object"""
        return EmailAddress.objects.fetch(self.cleaned_data['other_email'])

    def clean_other_fax(self):
        """Turn other fax into a Phone Number object"""
        if self.cleaned_data['other_fax']:
            fax, _ = PhoneNumber.objects.update_or_create(
                number=self.cleaned_data['other_fax'],
                defaults={'type': 'fax'},
            )
            return fax
        else:
            return self.cleaned_data['other_fax']
