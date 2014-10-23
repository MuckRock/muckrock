from django import forms
import autocomplete_light as autocomplete
from muckrock.foia.models import FOIARequest
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
    document = forms.CharField(widget=forms.Textarea(attrs = {'placeholder': u'Write one sentence that describing what you\'re looking for. The more specific you can be, the better.'}))
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
        widget=forms.TextInput(attrs = {'placeholder': 'Name the Agency'})
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
    agency = forms.CharField(widget=forms.TextInput(attrs = {'placeholder': 'Name an Agency' }))
    embargo = forms.BooleanField(required=False)
    
    def clean(self):
        data = self.cleaned_data
        embargo = data.get('embargo')
        if embargo and not self.request.user.can_embargo():
            error_msg = 'No state was selected'
            messages.error(request, error_msg)
            self._errors['embargo'] = self.error_class([error_msg])
        return self.cleaned_data
