"""
Forms for FOIA application
"""

from django import forms

import autocomplete_light as autocomplete
import inspect
import sys
from datetime import datetime, date, timedelta

from muckrock.agency.models import Agency, AgencyType
from muckrock.foia.models import FOIARequest, FOIAMultiRequest, FOIAFile, FOIANote, STATUS
from muckrock.foia.utils import make_template_choices
from muckrock.foia.validate import validate_date_order
from muckrock.jurisdiction.models import Jurisdiction

class RequestForm(forms.Form):
    # form data
        
    JURISDICTION_CHOICES = [
        ('f', 'Federal'),
        ('s', 'State'),
        ('l', 'Local')
    ]

    # form fields
    title = forms.CharField(widget=forms.TextInput(attrs = {'placeholder': 'Pick a Title'}))
    document = forms.CharField(widget=forms.Textarea(attrs = {'placeholder': u'Write one sentence describing what you\'re looking for. The more specific you can be, the better.'}))
    jurisdiction = forms.ChoiceField(
        choices=JURISDICTION_CHOICES,
        widget=forms.RadioSelect
    )
    state = autocomplete.ModelChoiceField(
        'StateAutocomplete',
        queryset=Jurisdiction.objects.filter(level='s', hidden=False), 
        required=False
    )
    local = autocomplete.ModelChoiceField(
        'LocalAutocomplete',
        queryset=Jurisdiction.objects.filter(level='l', hidden=False).order_by('parent', 'name'),
        required=False
    )
    agency = forms.CharField(
        label='Agency',
        widget=autocomplete.TextWidget('AgencyAutocomplete')
    ) 
    full_name = forms.CharField()
    email = forms.EmailField()

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
            error_msg = 'No state was selected'
            self._errors['state'] = self.error_class([error_msg])
        if jurisdiction == 'l' and not local:
            error_msg = 'No locality was selected'
            self._errors['local'] = self.error_class([error_msg])
        return self.cleaned_data

class RequestDraftForm(forms.Form):
    title = forms.CharField(widget=forms.TextInput(attrs = {'placeholder': 'Pick a Title'}))
    request = forms.CharField(widget=forms.Textarea())
    embargo = forms.BooleanField(
        required=False,
        help_text='Embargoing a request keeps it completely private from '
                  'other users until the embargo date you set. '
                  'You may change this whenever you want.'
    )

class MultiRequestForm(forms.ModelForm):
    """A form for a multi-Request"""

    title = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Pick a Title'})
    )
    requested_docs = forms.CharField(
        label='Request',
        widget=forms.Textarea()
    )
    agencies = forms.ModelMultipleChoiceField(
        label='Agencies',
        queryset=Agency.objects.filter(approved=True)
    )

    class Meta:
        # pylint: disable=R0903
        model = FOIAMultiRequest
        fields = ['title', 'requested_docs', 'agencies']
        
class MultiRequestDraftForm(forms.ModelForm):
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
        # pylint: disable=R0903
        model = FOIAMultiRequest
        fields = ['title', 'requested_docs', 'embargo']

class ListFilterForm(forms.Form):
    status = forms.ChoiceField(
        choices=STATUS,
        required=False
    )
    agency = forms.ModelChoiceField(
        required=False,
        queryset=Agency.objects.all(),
        widget=autocomplete.ChoiceWidget('AgencyAutocomplete'))
    jurisdiction = forms.ModelChoiceField(
        required=False,
        queryset=Jurisdiction.objects.all(),
        widget=autocomplete.ChoiceWidget('JurisdictionAutocomplete'))

    order = forms.ChoiceField(
        required=False,
        choices=(('asc', 'Ascending'), ('desc', 'Descending'))
    )
    sort = forms.ChoiceField(
        required=False,
        choices=(
            ('title', 'Title'),
            ('date_submitted', 'Date'),
            ('times_viewed', 'Popularity')
        )
    )

class MyListFilterForm(ListFilterForm):
    sort = forms.ChoiceField(
        required=False,
        choices=(
            ('title', 'Title'),
            ('date_submitted', 'Date'),
            ('times_viewed', 'Popularity'),
            ('read_status', 'Read Status')
        )
    )

class FOIAEmbargoForm(forms.ModelForm):
    """A form to update the embargo status of a FOIA Request"""
    embargo = forms.BooleanField(
        label='Embargo?',
        required=False,
        help_text=(
            'Embargoing a request keeps it completely private from other '
            'users until the embargo date you set. You may change this '
            'whenever you want.'
        )
    )
    date_embargo = forms.DateField(
        label='Embargo date',
        required=False,
        widget=forms.TextInput(attrs={'class': 'datepicker'})
    )
    
    def clean(self):
        """Checks if date embargo is necessary and if it is within 30 days"""
        embargo = self.cleaned_data.get('embargo')
        date_embargo = self.cleaned_data.get('date_embargo')
        finished_status = ['rejected', 'no_docs', 'done', 'partial', 'abandoned']
        if embargo and self.instance.status in finished_status:
            if not date_embargo:
                error_msg = 'Embargo date is required for finished requests'
                self._errors['date_embargo'] = self.error_class([error_msg])
            elif date_embargo > date.today() + timedelta(30):
                error_msg = 'Embargo date must be within 30 days of today'
                self._errors['date_embargo'] = self.error_class([error_msg])
        return self.cleaned_data

    class Meta:
        # pylint: disable=R0903
        model = FOIARequest
        fields = ['embargo', 'date_embargo']

class FOIADeleteForm(forms.Form):
    """Form to confirm deleting a FOIA Request"""
    confirm = forms.BooleanField(
        label='Are you sure you want to delete this FOIA request?',
        help_text='This cannot be undone!'
    )

FOIAFileFormSet = forms.models.modelformset_factory(FOIAFile, fields=('ffile',))

class FOIANoteForm(forms.ModelForm):
    """A form for a FOIA Note"""
    class Meta:
        # pylint: disable=R0903
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
