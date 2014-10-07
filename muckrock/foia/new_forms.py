from django import forms
import autocomplete_light as autocomplete
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.agency.models import Agency

class RequestForm(forms.Form):
    # form data
    JURISDICTION_CHOICES = [
        ('f', 'Federal'),
        ('s', 'State'),
        ('l', 'Local')
    ]

    # form fields
    title = forms.CharField(widget=forms.TextInput(attrs = {'placeholder': 'Pick a Title'}))
    document = forms.CharField(widget=forms.Textarea(attrs = {'placeholder': 'Write one sentence describing the specific document you are after.'}))
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
    agency = autocomplete.ModelChoiceField(
        'AgencyAutocomplete',
        queryset=Agency.objects.all()
    ) 
    
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