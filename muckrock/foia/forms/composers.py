"""
FOIA forms for composing requests
"""

# Django
from django import forms
from django.contrib.auth.models import User
from django.db.models import Q

# Standard Library
import re

# Third Party
from autocomplete_light import shortcuts as autocomplete_light
from autocomplete_light.contrib.taggit_field import TaggitField

# MuckRock
from muckrock.agency.models import Agency
from muckrock.foia.fields import ComposerAgencyField
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
    agencies = ComposerAgencyField(
        queryset=Agency.objects.get_approved(),
        widget=autocomplete_light.
        MultipleChoiceWidget('AgencyComposerAutocomplete'),
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
    action = forms.ChoiceField(
        choices=[
            ('save', 'Save'),
            ('submit', 'Submit'),
            ('delete', 'Delete'),
        ],
        required=True,
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
        self.user = kwargs.pop('user')
        super(ComposerForm, self).__init__(*args, **kwargs)
        if self.user.is_authenticated:
            del self.fields['full_name']
            del self.fields['email']
            del self.fields['newsletter']
        if not self.user.has_perm('foia.embargo_foiarequest'):
            del self.fields['embargo']
        self.fields['parent'
                    ].queryset = (FOIAComposer.objects.get_viewable(self.user))
        self.fields['agencies'].user = self.user
        self.fields['agencies'].queryset = (
            Agency.objects.get_approved_and_pending(self.user)
        )

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

    def clean(self):
        """Check cross field dependencies"""
        cleaned_data = super(ComposerForm, self).clean()
        if (
            cleaned_data['action'] == 'submit'
            and not self.cleaned_data['agencies']
        ):
            self.add_error(
                'agencies',
                'You must select at least one agency before submitting',
            )


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
