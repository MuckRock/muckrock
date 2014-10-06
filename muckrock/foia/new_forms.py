from django import forms
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
    title = forms.CharField(widget=forms.TextInput(attrs = {'placeholder': 'Choose a Short Title'}))
    document = forms.CharField(widget=forms.Textarea(attrs = {'placeholder': 'One sentence describing the specific document you are after.'}))
    jurisdiction = forms.ChoiceField(
        choices=JURISDICTION_CHOICES,
        widget=forms.RadioSelect
    )
    state = forms.ModelChoiceField(
        label='State',
        required=False,
        queryset=Jurisdiction.objects.filter(level='s').order_by('name'),
        widget=forms.Select(),
    )
    local = forms.ModelChoiceField(
        label='Local',
        required=False,
        queryset=Jurisdiction.objects.filter(level='l').order_by('parent', 'name'),
        widget=forms.Select(),
    )
    agency = forms.ModelChoiceField(
        label='Agency',
        required=False,
        queryset=Agency.objects.order_by('jurisdiction', 'name'),
        widget=forms.Select(),
    ) 
    
    def clean(self):
        jurisdiction = self.cleaned_data.get('jurisdiction')
        if jurisdiction == 's' and not state:
            error_msg = 'No state was selected'
            self._errors['state'] = self.error_class([error_msg])
        if jurisdiction == 'l' and not local:
            error_msg = 'No locality was selected'
            self._errors['local'] = self.error_class([error_msg])
        return self.cleaned_data