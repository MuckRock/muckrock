"""
FOIA forms for composing requests
"""

# Django
from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.utils.text import slugify

# Third Party
from autocomplete_light import shortcuts as autocomplete_light
from autocomplete_light.contrib.taggit_field import TaggitField

# MuckRock
from muckrock.accounts.utils import mailchimp_subscribe, miniregister
from muckrock.agency.models import Agency
from muckrock.foia.models import FOIAMultiRequest, FOIARequest
from muckrock.forms import TaggitWidget
from muckrock.jurisdiction.models import Jurisdiction


class RequestForm(forms.Form):
    """This form creates new, single MuckRock requests"""

    JURISDICTION_CHOICES = [('f', 'Federal'), ('s', 'State'), ('l', 'Local')]

    title = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'Add a subject'
        }),
        max_length=255,
    )
    document_placeholder = (
        'Write one sentence describing what you\'re looking for. '
        'The more specific you can be, the better.'
    )
    document = forms.CharField(
        widget=forms.Textarea(attrs={
            'placeholder': document_placeholder
        })
    )
    jurisdiction = forms.ChoiceField(
        choices=JURISDICTION_CHOICES, widget=forms.RadioSelect
    )
    state = autocomplete_light.ModelChoiceField(
        'StateAutocomplete',
        queryset=Jurisdiction.objects.filter(level='s', hidden=False),
        required=False
    )
    local = autocomplete_light.ModelChoiceField(
        'JurisdictionLocalAutocomplete',
        queryset=Jurisdiction.objects.filter(level='l', hidden=False),
        required=False
    )
    agency = autocomplete_light.ModelChoiceField(
        'AgencySimpleAgencyAutocomplete',
        queryset=Agency.objects.get_approved(),
    )
    full_name = forms.CharField(label='Full Name or Handle (Public)')
    email = forms.EmailField(max_length=75)
    newsletter = forms.BooleanField(
        initial=True,
        required=False,
        label='Get MuckRock\'s weekly newsletter with '
        'FOIA news, tips, and more',
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(RequestForm, self).__init__(*args, **kwargs)
        if self.request and self.request.user.is_authenticated:
            del self.fields['full_name']
            del self.fields['email']
            del self.fields['newsletter']
        self.jurisdiction = None

    def full_clean(self):
        """Remove required from agency"""
        # We want "required" attribute on the field, but we might take the text value
        # instead of the drop down value
        self.fields['agency'].required = False
        super(RequestForm, self).full_clean()

    def clean(self):
        """Ensure the jurisdiction and agency were set correctly"""
        self.jurisdiction = self.get_jurisdiction()
        if self.jurisdiction:
            self.cleaned_data['agency'] = self.get_agency()
        return self.cleaned_data

    def clean_email(self):
        """Do a case insensitive uniqueness check"""
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                'User with this email already exists. Please login first.'
            )
        return email

    def get_jurisdiction(self):
        """Get the jurisdiction from the correct field"""
        jurisdiction = self.cleaned_data.get('jurisdiction')
        state = self.cleaned_data.get('state')
        local = self.cleaned_data.get('local')
        if jurisdiction == 'f':
            return Jurisdiction.objects.filter(level='f').first()
        elif jurisdiction == 's' and not state:
            self.add_error('state', 'No state was selected')
            return None
        elif jurisdiction == 's' and state:
            return state
        elif jurisdiction == 'l' and not local:
            self.add_error('local', 'No locality was selected')
            return None
        elif jurisdiction == 'l' and local:
            return local

    def get_agency(self):
        """Get the agency and create a new one if necessary"""
        agency = self.cleaned_data.get('agency')
        agency_autocomplete = self.request.POST.get('agency-autocomplete', '')
        agency_autocomplete = agency_autocomplete.strip()
        if agency is None and agency_autocomplete:
            # See if the passed in agency name matches a valid known agency
            agency = (
                Agency.objects.get_approved().filter(
                    name__iexact=agency_autocomplete,
                    jurisdiction=self.jurisdiction,
                ).first()
            )
            # if not, create a new one
            if agency is None and len(agency_autocomplete) < 256:
                agency = Agency.objects.create_new(
                    agency_autocomplete,
                    self.jurisdiction,
                    self.request.user,
                )
            elif agency is None and len(agency_autocomplete) >= 256:
                self.add_error(
                    'agency', 'Agency name must be less than 256 characters'
                )
                return None
        elif agency is None:
            self.add_error('agency', 'Please select an agency')
            return None
        elif agency.exempt:
            self.add_error(
                'agency',
                'The agency you selected is exempt from '
                'public records requests',
            )
            return None
        return agency

    def make_user(self, data):
        """Miniregister a new user if necessary"""
        user, password = miniregister(data['full_name'], data['email'])
        user = authenticate(
            username=user.username,
            password=password,
        )
        login(self.request, user)
        if data.get('newsletter'):
            mailchimp_subscribe(self.request, user.email)

    def process(self, parent):
        """Create the new request"""
        if self.request.user.is_anonymous():
            self.make_user(self.cleaned_data)
        agency = self.cleaned_data['agency']
        proxy_info = agency.get_proxy_info()
        if 'warning' in proxy_info:
            messages.warning(self.request, proxy_info['warning'])
        foia = FOIARequest.objects.create(
            user=self.request.user,
            status='started',
            title=self.cleaned_data['title'],
            jurisdiction=self.jurisdiction,
            slug=slugify(self.cleaned_data['title']) or 'untitled',
            agency=agency,
            requested_docs=self.cleaned_data['document'],
            description=self.cleaned_data['document'],
            parent=parent,
            missing_proxy=proxy_info['missing_proxy'],
        )
        foia.create_initial_communication(
            proxy_info.get('from_user', self.request.user),
            proxy_info['proxy'],
        )
        return foia


class RequestDraftForm(forms.Form):
    """Presents limited information from created single request for editing"""
    title = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'Pick a Title'
        }),
        max_length=255,
    )
    request = forms.CharField(widget=forms.Textarea())
    embargo = forms.BooleanField(
        required=False,
        help_text='Embargoing a request keeps it completely private from '
        'other users until the embargo date you set. '
        'You may change this whenever you want.'
    )


class MultiRequestForm(forms.ModelForm):
    """A form for a multi-request"""

    requested_docs = forms.CharField(label='Request', widget=forms.Textarea())
    agencies = forms.ModelMultipleChoiceField(
        queryset=Agency.objects.get_approved(),
        required=True,
        widget=autocomplete_light.
        MultipleChoiceWidget('AgencyMultiRequestAutocomplete'),
    )
    parent = forms.ModelChoiceField(
        queryset=FOIAMultiRequest.objects.none(),
        required=False,
        widget=forms.HiddenInput(),
    )

    class Meta:
        model = FOIAMultiRequest
        fields = ['title', 'requested_docs', 'agencies', 'parent']
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Pick a Title'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(MultiRequestForm, self).__init__(*args, **kwargs)
        self.fields['parent'].queryset = FOIAMultiRequest.objects.filter(
            user=user
        )


class MultiRequestDraftForm(forms.ModelForm):
    """Presents info from created multi-request for editing"""
    title = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'Pick a Title'
        })
    )
    tags = TaggitField(
        widget=TaggitWidget(
            'TagAutocomplete',
            attrs={
                'placeholder': 'Search tags',
                'data-autocomplete-minimum-characters': 1
            }
        ),
        help_text='Separate tags with commas.',
        required=False,
    )
    requested_docs = forms.CharField(label='Request', widget=forms.Textarea())
    embargo = forms.BooleanField(
        required=False,
        help_text='Embargoing a request keeps it completely private from '
        'other users until the embargo date you set.  '
        'You may change this whenever you want.'
    )

    class Meta:
        model = FOIAMultiRequest
        fields = ['title', 'tags', 'requested_docs', 'embargo']
