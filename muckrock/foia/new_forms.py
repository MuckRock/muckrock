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
    title = forms.CharField()
    document = forms.CharField(widget=forms.Textarea(attrs = {'placeholder': 'One sentence describing the specific document you are after.'}))
    jurisdiction = forms.ChoiceField(choices=JURISDICTION_CHOICES)
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
    agency = forms.CharField()
    '''
    agency = forms.ModelChoiceField(
        label='Agency',
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': 'combobox'}),
        help_text=('Select one of the agencies for the jurisdiction you '
                   'have chosen, or write in the correct agency if known.')
    )
    '''
    
    def clean(self):
        jurisdiction = self.cleaned_data.get('jurisdiction')
        if jurisdiction == 's' and not state:
            error_msg = 'No state was selected'
            self._errors['state'] = self.error_class([error_msg])
        if jurisdiction == 'l' and not local:
            error_msg = 'No locality was selected'
            self._errors['local'] = self.error_class([error_msg])
        return self.cleaned_data