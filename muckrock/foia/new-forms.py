from django import forms
import autocomplete_light as autocomplete

class RequestForm(forms.Form):
    title = forms.CharField()
    request = forms.CharField(widget=forms.Textarea)

class JurisdictionForm(forms.Form):
    states = Jurisdiction.objects.filter(level='s', hidden=False)
    localities = Jurisdiction.objects.filter(level='l', hidden=False)
    
    is_federal = models.BooleanField()
    is_state = models.BooleanField()
    is_local = models.BooleanField()
    state = autocomplete.ModelChoiceField(
        'StateAutocomplete',
        queryset=states,
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
        is_state, is_local = data.get('is_state'), data.get('is_local')
        state, local = data.get('state'), data.get('local')
        if is_state and not state:
            error_msg = 'No state was selected'
            self._errors['state'] = self.error_class([error_msg])
        if is_local and not local and not is_state:
            error_msg = 'No locality was selected'
            self._errors['local'] = self.error_class([error_msg])
        return self.cleaned_data

class EmbargoForm(forms.Form):
    embargo = forms.CheckboxField()
    embargo_date = models.DateField()
    
    def __init__(self, user, *args, **kwargs):
        super(ProjectTypeForm, self).__init__(*args, **kwargs)
        self.user = user
    def clean(self):
        