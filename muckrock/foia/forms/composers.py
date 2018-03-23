"""
FOIA forms for composing requests
"""

# Django
from django import forms
from django.contrib.auth.models import User
from django.utils.text import slugify

# Third Party
from autocomplete_light import shortcuts as autocomplete_light
from autocomplete_light.contrib.taggit_field import TaggitField

# MuckRock
from muckrock.agency.models import Agency
from muckrock.foia.models import FOIAComposer, FOIAMultiRequest
from muckrock.forms import TaggitWidget


class ComposerForm(forms.ModelForm):
    """This form creates and updates FOIA composers"""

    title = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'Add a title'
        }),
        max_length=255,
    )
    requested_docs = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'placeholder':
                    'Write a short description of the documents you are '
                    'looking for. The more specific you can be, the better.'
            }
        )
    )
    # XXX agencies is not required to save, but is required to submit
    agencies = autocomplete_light.ModelMultipleChoiceField(
        # XXX rename this autocomplete
        'AgencyMultiRequestAutocomplete',
        queryset=Agency.objects.get_approved(),
    )
    embargo = forms.BooleanField(
        required=False,
        help_text='Embargoing a request keeps it completely private from '
        'other users until the embargo date you set. '
        'You may change this whenever you want.'
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
    parent = forms.ModelChoiceField(
        queryset=FOIAComposer.objects.none(),
        required=False,
        widget=forms.HiddenInput(),
    )

    full_name = forms.CharField(label='Full Name or Handle (Public)')
    email = forms.EmailField(max_length=75)
    newsletter = forms.BooleanField(
        initial=True,
        required=False,
        label='Get MuckRock\'s weekly newsletter with '
        'FOIA news, tips, and more',
    )

    class Meta:
        model = FOIAComposer
        fields = [
            'title',
            'requested_docs',
            'agencies',
            'embargo',
            'tags',
            'parent',
            'full_name',
            'email',
            'newsletter',
        ]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(ComposerForm, self).__init__(*args, **kwargs)
        if user.is_authenticated:
            del self.fields['full_name']
            del self.fields['email']
            del self.fields['newsletter']
        # XXX check/enforce embargo permissions here
        # XXX
        #self.fields['parent'].queryset = FOIAComposer.objects.viewable_by(user)
        self.fields['parent'].queryset = FOIAComposer.objects.all()

    def clean_email(self):
        """Do a case insensitive uniqueness check"""
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                'User with this email already exists. Please login first.'
            )
        return email

    def clean_title(self):
        """Make sure we have a non-blank(ish) title"""
        title = self.cleaned_data['title'].strip()
        if title:
            return title
        else:
            return 'Untitled'

    def get_agency(self):
        """Get the agency and create a new one if necessary"""
        # XXX need to completely rethink how new agencies work
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
