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

class RequestUpdateForm(forms.Form):
    title = forms.CharField(widget=forms.TextInput(attrs = {'placeholder': 'Pick a Title'}))
    request = forms.CharField(widget=forms.Textarea())
    embargo = forms.BooleanField(
        required=False,
        help_text='Embargoing a request keeps it completely private from '
                  'other users until the embargo date you set. '
                  'You may change this whenever you want.'
    )
    
    def clean(self):
        data = self.cleaned_data
        embargo = data.get('embargo')
        if embargo and not self.request.user.can_embargo():
            error_msg = 'Only Pro users may embargo their requests.'
            messages.error(request, error_msg)
            self._errors['embargo'] = self.error_class([error_msg])
        return self.cleaned_data

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

class FOIARequestForm(forms.ModelForm):
    """A form for a FOIA Request"""
    agency = forms.ModelChoiceField(
        label='Agency',
        required=False,
        queryset=Agency.objects.order_by('name'),
        widget=forms.Select(attrs={'class': 'combobox'}),
        help_text=('Select one of the agencies for the jurisdiction you '
                   'have chosen, or write in the correct agency if known.')
    )    
    embargo = forms.BooleanField(
        required=False,
        help_text=('Embargoing a request keeps it completely private from '
                   'other users until the embargo date you set. '
                   'You may change this whenever you want.')
    )
    request = forms.CharField(
        widget=forms.Textarea(attrs={'style': 'width:450px; height:200px;'})
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(FOIARequestForm, self).__init__(*args, **kwargs)
        if not (self.request and self.request.user.get_profile().can_embargo()):
            del self.fields['embargo']
            self.Meta.fields = ['title', 'agency']

    class Meta:
        # pylint: disable=R0903
        model = FOIARequest
        fields = ['title', 'agency', 'embargo']
        widgets = {
            'title': forms.TextInput(attrs={'style': 'width:450px;'}),
        }

class FOIAMultiRequestForm(forms.ModelForm):
    """A form for a FOIA Multi-Request"""

    embargo = forms.BooleanField(required=False,
                                 help_text='Embargoing a request keeps it completely private from '
                                           'other users until the embargo date you set.  '
                                           'You may change this whenever you want.')
    requested_docs = forms.CharField(label='Request',
        widget=forms.Textarea(attrs={'style': 'width:450px; height:50px;'}))

    class Meta:
        # pylint: disable=R0903
        model = FOIAMultiRequest
        fields = ['title', 'embargo', 'requested_docs']
        widgets = {'title': forms.TextInput(attrs={'style': 'width:450px;'})}
        
class FOIAMultipleSubmitForm(forms.Form):
    """Form to select multiple agencies to submit to"""
    agency_type = forms.ModelChoiceField(queryset=AgencyType.objects.all(), required=False)
    jurisdiction = forms.ModelChoiceField(queryset=Jurisdiction.objects.all(), required=False)

class AgencyConfirmForm(forms.Form):
    """Confirm agencies for a multiple submit"""
    def __init__(self, *args, **kwargs):
        self.queryset = kwargs.pop('queryset', [])
        super(AgencyConfirmForm, self).__init__(*args, **kwargs)
        self.fields['agencies'].queryset = self.queryset
    class AgencyChoiceField(forms.ModelMultipleChoiceField):
        """Add jurisdiction to agency label"""
        def label_from_instance(self, obj):
            return '%s - %s' % (obj.name, obj.jurisdiction)
    agencies = AgencyChoiceField(queryset=None, widget=forms.CheckboxSelectMultiple)

class FOIAEmbargoForm(forms.ModelForm):
    """A form to update the embargo status of a FOIA Request"""

    embargo = forms.BooleanField(required=False,
                                 help_text='Embargoing a request keeps it completely private from '
                                           'other users until the embargo date you set.  '
                                           'You may change this whenever you want.')

    class Meta:
        # pylint: disable=R0903
        model = FOIARequest
        fields = ['embargo']

class FOIAEmbargoDateForm(FOIAEmbargoForm):
    """A form to update the embargo status of a FOIA Request"""

    date_embargo = forms.DateField(label='Embargo date', required=False,
                                   widget=forms.TextInput(attrs={'class': 'datepicker'}))

    def clean(self):
        """date_embargo is required if embargo is checked and must be within 30 days"""

        embargo = self.cleaned_data.get('embargo')
        date_embargo = self.cleaned_data.get('date_embargo')

        if embargo:
            if not date_embargo:
                self._errors['date_embargo'] = self.error_class(
                        ['Embargo date is required if embargo is selected'])
            elif date_embargo > date.today() + timedelta(30):
                self._errors['date_embargo'] = self.error_class(
                        ['Embargo date must be within 30 days of today'])

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
