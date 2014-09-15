from django import forms
import autocomplete_light as autocomplete
from muckrock.jurisdiction.models import Jurisdiction

class RequestForm(forms.Form):
    title = forms.CharField()
    request = forms.CharField(widget=forms.Textarea)

class JurisdictionForm(forms.Form):
    jurisdictions = []
    states = Jurisdiction.objects.filter(level='s', hidden=False)
    localities = Jurisdiction.objects.filter(level='l', hidden=False)
    
    STATES_CHOICES = [(s.abbrev, s.name) for s in states]
    
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
    
    def get_jurisdiction_list(self):
        """Creates a list of all chosen jurisdictions"""
        j_list = []
        data = self.cleaned_data
        is_state, is_local = data.get('is_state'), data.get('is_local')
        state, local = data.get('state'), data.get('local')
        if data.get('is_federal'):
            j = Jurisdiction.objects.filter(level='f', hidden=False)
            j_list.append(j)
        if is_state:
            j = Jurisdiction.objects.filter(level='s', full_name=state)
            j_list.append(j)
            if is_local and not local:
                k = Jurisdiction.objects.filter(level='l', parent=state)
                j_list.append(k)
        if is_local:
            j = Jurisdiction.objects.filter(level='l', full_name=local)
            j_list.append(j)
        return j_list
    
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
        self.jurisdictions = self.get_jurisdiction_list()
        return self.cleaned_data
        
class AgencyForm(forms.Form):

    AGENCY_CHOICES = []
    agencies = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(),
        choices=AGENCY_CHOICES
    )
    
    def clean(self):
        """Ensures at least one agency is chosen"""
        agencies = self.cleaned_data.get('agencies')
        if agencies is None or len(agencies) == 0:
            error_msg = 'You must choose at least one agency.'
            self._errors['agencies'] = self.error_class([error_msg])
        return self.cleaned_data
  
    def __init__(self, *args, **kwargs):
        try:
            jurisdictions = kwargs.pop('j')
            for jurisdiction in jurisdictions:
                agencies = Agency.objects.filter(jurisdiction=jurisdiction)
                for agency in agencies:
                    self.AGENCY_CHOICES.append((agency.name))
        except KeyError as e:
            print e
        super(AgencyForm, self).__init__(*args, **kwargs)


    def _get_agencies(self):
        """Get and cache the agencies selected in the submit step"""
        if self.jurisdictions:
            agencies = Agency.objects.get_approved()
            if agency_type:
                agencies = agencies.filter(types=agency_type)
            if jurisdiction and jurisdiction.level == 's':
                agencies = agencies.filter(Q(jurisdiction=jurisdiction) |
                                           Q(jurisdiction__parent=jurisdiction))
            elif jurisdiction:
                agencies = agencies.filter(jurisdiction=jurisdiction)
            self.agencies = agencies
            return agencies
        else:
            return None

class EmbargoForm(forms.Form):
    embargo = forms.BooleanField()
    embargo_date = forms.DateField()
    
    def __init__(self, user, *args, **kwargs):
        super(ProjectTypeForm, self).__init__(*args, **kwargs)
        self.user = user

class ConfirmationForm(forms.Form):
    submit = forms.BooleanField()