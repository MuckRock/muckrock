from django import forms
import autocomplete_light as autocomplete
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.agency.models import Agency

class RequestForm(forms.Form):
    title = forms.CharField()
    document = forms.CharField(widget=forms.Textarea)

class JurisdictionForm(forms.Form):
    states = Jurisdiction.objects.filter(level='s', hidden=False)
    localities = Jurisdiction.objects.filter(level='l', hidden=False)
    
    STATES_CHOICES = [('', '--Pick a State--')] + [(s.abbrev, s.name) for s in states]
    
    is_federal = forms.BooleanField(required=False)
    is_state = forms.BooleanField(required=False)
    is_local = forms.BooleanField(required=False)
    state = forms.ChoiceField(
        choices=STATES_CHOICES,
        required=False
    )
    local = autocomplete.ModelChoiceField(
        'LocalAutocomplete',
        queryset=localities.order_by('parent', 'name'),
        required=False
    )
    
    def clean(self):
        """Ensures conditional fields are filled in"""
        data = self.cleaned_data
        is_federal = data.get('is_federal')
        is_state, is_local = data.get('is_state'), data.get('is_local')
        state, local = data.get('state'), data.get('local')
        if not is_federal and not is_state and not is_local:
            error_msg = 'No jurisdiction was selected'
            self._errors['federal'] = self.error_class([error_msg])
        if is_state and not state:
            error_msg = 'No state was selected'
            self._errors['state'] = self.error_class([error_msg])
        if not is_state and is_local and not local:
            error_msg = 'No locality was selected'
            self._errors['local'] = self.error_class([error_msg])
        return self.cleaned_data
        
class AgencyForm(forms.Form):

    other = forms.CharField(required=False)
    
    def clean(self):
        """Ensures at least one agency is chosen"""
        agencies = self.cleaned_data.get('agencies')
        if not agencies or not self.other:
            error_msg = 'You must add at least one agency.'
            self._errors['agencies'] = self.error_class([error_msg])
        return self.cleaned_data
  
    def __init__(self, *args, **kwargs):
        try:
            initial = kwargs.pop('initial')
            jurisdictions = initial['jurisdictions']
        except KeyError as e:
            print 'KeyError: ' + e
        super(AgencyForm, self).__init__(*args, **kwargs)
        
        agencies = []      
        for jurisdiction in jurisdictions:
            agencies += Agency.objects.filter(jurisdiction=jurisdiction)
        for agency in agencies:
            # identifier = agency.name
            self.fields[agency.name] = forms.BooleanField(required=False)
        
    
    


class ConfirmationForm(forms.Form):

    embargo = forms.BooleanField()
    embargo_date = forms.DateField()
    submit = forms.BooleanField()
    
    def __init__(self, *args, **kwargs):
        try:
            initial = kwargs.pop('initial')
            self.user = initial['user']
            self.title = initial['title']
            self.request = initial['document']
            self.agencies = initial['agencies']
        except KeyError as e:
            print 'KeyError: ' + e
        super(AgencyForm, self).__init__(*args, **kwargs)