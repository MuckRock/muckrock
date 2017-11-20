"""
Forms for FOIA application
"""

from django import forms
from django.contrib.auth.models import User

from autocomplete_light import shortcuts as autocomplete_light
from datetime import date, timedelta
import phonenumbers

from muckrock.agency.models import Agency
from muckrock.communication.models import EmailAddress, PhoneNumber
from muckrock.foia.models import (
        FOIARequest,
        FOIAMultiRequest,
        FOIACommunication,
        FOIAFile,
        FOIANote,
        STATUS,
        )
from muckrock.forms import MRFilterForm, TaggitWidget
from muckrock.jurisdiction.models import Jurisdiction

AGENCY_STATUS = [
    ('processed', 'Further Response Coming'),
    ('fix', 'Fix Required'),
    ('payment', 'Payment Required'),
    ('rejected', 'Rejected'),
    ('no_docs', 'No Responsive Documents'),
    ('done', 'Completed'),
    ('partial', 'Partially Completed'),
    ]


class RequestForm(forms.Form):
    """This form creates new, single MuckRock requests"""

    JURISDICTION_CHOICES = [
        ('f', 'Federal'),
        ('s', 'State'),
        ('l', 'Local')
    ]

    title = forms.CharField(
            widget=forms.TextInput(attrs={'placeholder': 'Add a subject'}),
            max_length=255,
            )
    document_placeholder = (
        'Write one sentence describing what you\'re looking for. '
        'The more specific you can be, the better.'
    )
    document = forms.CharField(widget=forms.Textarea(attrs={'placeholder': document_placeholder}))
    jurisdiction = forms.ChoiceField(
        choices=JURISDICTION_CHOICES,
        widget=forms.RadioSelect
    )
    state = autocomplete_light.ModelChoiceField(
        'StateAutocomplete',
        queryset=Jurisdiction.objects.filter(level='s', hidden=False),
        required=False
    )
    local = autocomplete_light.ModelChoiceField(
        'JurisdictionLocalAutocomplete',
        required=False
    )
    agency = forms.CharField(
        label='Agency',
        widget=autocomplete_light.TextWidget(
            'AgencySimpleAgencyAutocomplete',
            attrs={'placeholder': 'Type the agency\'s name'}),
        max_length=255)
    full_name = forms.CharField()
    email = forms.EmailField(max_length=75)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(RequestForm, self).__init__(*args, **kwargs)
        if self.request and self.request.user.is_authenticated():
            del self.fields['full_name']
            del self.fields['email']

    def clean(self):
        data = self.cleaned_data
        jurisdiction = data.get('jurisdiction')
        state = data.get('state')
        local = data.get('local')
        if jurisdiction == 's' and not state:
            error_msg = 'No state was selected.'
            self._errors['state'] = self.error_class([error_msg])
        if jurisdiction == 'l' and not local:
            error_msg = 'No locality was selected.'
            self._errors['local'] = self.error_class([error_msg])
        return self.cleaned_data

    def clean_email(self):
        """Do a case insensitive uniqueness check"""
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email):
            raise forms.ValidationError("User with this email already exists.  Please login first.")
        return email


class RequestDraftForm(forms.Form):
    """Presents limited information from created single request for editing"""
    title = forms.CharField(
            widget=forms.TextInput(attrs={'placeholder': 'Pick a Title'}),
            max_length=255,
            )
    request = forms.CharField(widget=forms.Textarea())
    embargo = forms.BooleanField(
        required=False,
        help_text='Embargoing a request keeps it completely private from '
                  'other users until the embargo date you set. '
                  'You may change this whenever you want.'
    )


class AgencyMultipleChoiceField(forms.MultipleChoiceField):
    """Custom multiple choice field that loads without any data"""
    def clean(self, value):
        # pylint: disable=no-self-use
        # pylint: disable=missing-docstring
        for agency_id in value:
            try:
                Agency.objects.get(pk=agency_id)
            except (Agency.DoesNotExist, ValueError):
                raise forms.ValidationError
        return value


class MultiRequestForm(forms.ModelForm):
    """A form for a multi-request"""

    requested_docs = forms.CharField(
        label='Request',
        widget=forms.Textarea()
    )

    class Meta:
        # pylint: disable=too-few-public-methods
        model = FOIAMultiRequest
        fields = ['title', 'requested_docs', 'agencies']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Pick a Title'}),
            'agencies': autocomplete_light.MultipleChoiceWidget('AgencyMultiRequestAutocomplete')
        }


class MultiRequestDraftForm(forms.ModelForm):
    """Presents info from created multi-request for editing"""
    title = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Pick a Title'})
    )
    requested_docs = forms.CharField(
        label='Request',
        widget=forms.Textarea()
    )
    embargo = forms.BooleanField(
        required=False,
        help_text='Embargoing a request keeps it completely private from '
                  'other users until the embargo date you set.  '
                  'You may change this whenever you want.'
    )
    class Meta:
        # pylint: disable=too-few-public-methods
        model = FOIAMultiRequest
        fields = ['title', 'requested_docs', 'embargo']


class RequestFilterForm(MRFilterForm):
    """Provides options for filtering list by request characteristics"""
    status_filters = [('', 'All Status')] + list(STATUS)
    status = forms.ChoiceField(
        choices=status_filters,
        required=False
    )


class FOIAEstimatedCompletionDateForm(forms.ModelForm):
    """Form to change an estimaged completion date."""
    date_estimate = forms.DateField(
        label='Estimated completion date',
        help_text='The est. completion date is declared by the agency.',
        widget=forms.DateInput(format='%m/%d/%Y', attrs={'placeholder': 'mm/dd/yyyy'}),
        input_formats=[
            '%Y-%m-%d',      # '2006-10-25'
            '%m/%d/%Y',      # '10/25/2006'
            '%m/%d/%y',      # '10/25/06'
            '%m-%d-%Y',      # '10-25-2006',
            '%m-%d-%y',      # '10-25-06',
            '%b %d %Y',      # 'Oct 25 2006'
            '%b %d, %Y',     # 'Oct 25, 2006'
            '%d %b %Y',      # '25 Oct 2006'
            '%d %b, %Y',     # '25 Oct, 2006'
            '%B %d %Y',      # 'October 25 2006'
            '%B %d, %Y',     # 'October 25, 2006'
            '%d %B %Y',      # '25 October 2006'
            '%d %B, %Y']     # '25 October, 2006'
    )

    class Meta:
        model = FOIARequest
        fields = ['date_estimate']


class FOIAEmbargoForm(forms.Form):
    """Form to configure an embargo on a request"""
    permanent_embargo = forms.BooleanField(
        required=False,
        label='Make permanent',
        help_text='A permanent embargo will never expire.',
        widget=forms.CheckboxInput()
    )

    date_embargo = forms.DateField(
        required=False,
        label='Expiration date',
        help_text='Embargo duration are limited to a maximum of 30 days.',
        widget=forms.DateInput(attrs={
            'class': 'datepicker',
            'placeholder': 'Pick a date'
        })
    )

    def clean_date_embargo(self):
        """Checks if date embargo is within 30 days"""
        date_embargo = self.cleaned_data['date_embargo']
        max_duration = date.today() + timedelta(30)
        if date_embargo and date_embargo > max_duration:
            error_msg = 'Embargo expiration date must be within 30 days of today'
            self._errors['date_embargo'] = self.error_class([error_msg])
        return date_embargo


class FOIAFileForm(forms.ModelForm):
    """A form for a FOIA File"""
    ffile = forms.FileField(
            label='File',
            required=False,
            )

    class Meta:
        model = FOIAFile
        fields = ['ffile']


class FOIANoteForm(forms.ModelForm):
    """A form for a FOIA Note"""
    class Meta:
        # pylint: disable=too-few-public-methods
        model = FOIANote
        fields = ['note']
        widgets = {'note': forms.Textarea(attrs={'class': 'prose-editor'})}


class FOIAAccessForm(forms.Form):
    """Form to add editors or viewers to a request."""
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=autocomplete_light.MultipleChoiceWidget('UserRequestSharingAutocomplete')
    )
    access_choices = [
        ('edit', 'Can Edit'),
        ('view', 'Can View'),
    ]
    access = forms.ChoiceField(choices=access_choices)


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
            widget=forms.NumberInput(attrs={'class': 'currency-field'}),
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
        if self.foia:
            if self.foia.portal:
                via = 'portal'
            elif self.foia.email:
                via = 'email'
            elif self.foia.fax:
                via = 'fax'
            else:
                via = 'snail'
            initial.update({
                    'via': via,
                    'email': self.foia.email,
                    'fax': self.foia.fax,
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
        if cleaned_data['via'] == 'portal' and not self.foia.agency.portal:
            self.add_error(
                    'via',
                    'This request\'s agency does not use a portal',
                    )
        elif cleaned_data['via'] == 'email' and not cleaned_data['email']:
            self._clean_email(cleaned_data)
        elif cleaned_data['via'] == 'fax' and not cleaned_data['fax']:
            self._clean_fax(cleaned_data)
        return cleaned_data

    def _clean_email(self, cleaned_data):
        """Attempt to clean the email during full form clean"""
        if cleaned_data['email-autocomplete']:
            email = EmailAddress.objects.fetch(cleaned_data['email-autocomplete'])
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
                number = phonenumbers.parse(cleaned_data['fax-autocomplete'], 'US')
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
                    ])
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
