from django import forms
import autocomplete_light as autocomplete
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.agency.models import Agency

class DocumentForm(forms.Form):
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

    other = forms.CharField(
        required=False,
        help_text='Separate agency names with commas'
    )
    
    def clean(self):
        """Ensures at least one agency is chosen"""
        agencies = [key for key, value in self.cleaned_data.items() if key is not 'other' and value is not False]
        if not agencies:
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
            self.fields[agency.name] = forms.BooleanField(required=False)
        
class ConfirmationForm(forms.Form):

    embargo = forms.BooleanField(required=False)
    embargo_expiration = forms.DateField(required=False)
    
    def _compose_preview(self, document, agencies, user):
        intro = 'This is a request under the Freedom of Information Act.'
        waiver = ('I also request that, if appropriate, fees be waived as I '
                  'believe this request is in the public interest. '
                  'The requested documents  will be made available to the ' 
                  'general public free of charge as part of the public ' 
                  'information service at MuckRock.com, processed by a ' 
                  'representative of the news media/press and is made in the ' 
                  ' process of news gathering and not for commercial usage.')
        delay = '20 business days'
        
        if len(self.agencies) == 1:
            j = self.agencies[0].jurisdiction
            if j.get_intro():
                intro = j.get_intro()                
            if j.get_waiver():
                waiver = j.get_waiver()
            if j.get_days():
                delay = str(j.get_days())
        
        prepend = [intro + ' I hereby request the following records:']
        append = [waiver,
                 ('In the event that fees cannot be waived, I would be '
                  'grateful if you would inform me of the total charges in '     
                  'advance of fulfilling my request. I would prefer the '
                  'request filled electronically, by e-mail attachment if ' 
                  'available or CD-ROM if not.'),
                  ('Thank you in advance for your anticipated cooperation in '
                  'this matter. I look forward to receiving your response to ' 
                  'this request within %s, as the statute requires.' % delay )]
        if self.user:
            full_name = self.user.get_full_name()
            append.append('Sincerely,\n' + full_name)
        
        return prepend + [self.document] + append
    
    def clean(self):
        data = self.cleaned_data
        if data['embargo'] and not data['embargo_expiration']:
            error_msg = 'Embargoed requests must specify an expiration date.'
            self._errors['embargo_expiration'] = self.error_class([error_msg])
        return self.cleaned_data
    
    def __init__(self, *args, **kwargs):
        try:
            initial = kwargs.pop('initial')
            self.user = initial['user']
            self.title = initial['title']
            self.document = initial['document']
            self.agencies = initial['agencies']
            self.new_agencies = initial['new_agencies']
        except KeyError as e:
            print 'KeyError: ' + str(e)
        super(ConfirmationForm, self).__init__(*args, **kwargs)
        
        self.agency_names = [agency.name for agency in self.agencies] + \
                            self.new_agencies
        self.request_text = self._compose_preview(self.document,
                                                  self.agencies,
                                                  self.user)
        print self.request_text