"""
Forms for FOIA application
"""

from django import forms
from django.contrib.auth.models import User

from autocomplete_light import shortcuts as autocomplete_light
from datetime import date, timedelta

from muckrock.forms import MRFilterForm
from muckrock.agency.models import Agency
from muckrock.foia.models import FOIARequest, FOIAMultiRequest, FOIAFile, FOIANote, STATUS
from muckrock.jurisdiction.models import Jurisdiction

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
            'AgencyAutocomplete',
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


class FOIADeleteForm(forms.Form):
    """Form to confirm deleting a FOIA Request"""
    confirm = forms.BooleanField(
        label='Are you sure you want to delete this FOIA request?',
        help_text='This cannot be undone!'
    )

class FOIAFileForm(forms.ModelForm):
    """A form for a FOIA File"""
    ffile = forms.FileField(label='File', required=False)

    class Meta:
        model = FOIAFile
        fields = ['ffile']

FOIAFileFormSet = forms.models.modelformset_factory(FOIAFile, form=FOIAFileForm)

class FOIANoteForm(forms.ModelForm):
    """A form for a FOIA Note"""
    class Meta:
        # pylint: disable=too-few-public-methods
        model = FOIANote
        fields = ['note']
        widgets = {'note': forms.Textarea()}

class FOIAAdminFixForm(forms.ModelForm):
    """Form to email from the request's address"""
    class Meta:
        model = FOIARequest
        fields = ['from_email', 'email', 'other_emails', 'comm']

    from_email = forms.CharField(
        label='From',
        initial='MuckRock',
        required=False,
        help_text='Leaving blank will fill in with request owner.'
    )
    email = forms.EmailField(
        label='To',
        required=False,
        help_text='Leave blank to send to agency default.'
    )
    other_emails = forms.CharField(label='CC', required=False)
    comm = forms.CharField(label='Body', widget=forms.Textarea())
    snail_mail = forms.BooleanField(required=False, label='Snail Mail Only')

    def clean_other_emails(self):
        """Strips extra whitespace from email list"""
        other_emails = self.cleaned_data['other_emails']
        other_emails = other_emails.strip()
        return other_emails

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
