"""
FOIA forms used on the detail page
"""

# Django
from django import forms
from django.contrib.auth.models import User

# Standard Library
from datetime import date, timedelta

# Third Party
from autocomplete_light import shortcuts as autocomplete_light

# MuckRock
from muckrock.foia.models import FOIANote, FOIARequest, TrackingNumber
from muckrock.task.models import PUBLIC_FLAG_CATEGORIES


class FOIAEstimatedCompletionDateForm(forms.ModelForm):
    """Form to change an estimaged completion date."""
    date_estimate = forms.DateField(
        label='Estimated completion date',
        help_text='The est. completion date is declared by the agency.',
        widget=forms.DateInput(
            format='%m/%d/%Y', attrs={
                'placeholder': 'mm/dd/yyyy'
            }
        ),
    )

    class Meta:
        model = FOIARequest
        fields = ['date_estimate']


class FOIAEmbargoForm(forms.Form):
    """Form to configure an embargo on a request"""
    permanent_embargo = forms.BooleanField(
        required=False,
        label='Make permanent',
        help_text='A permanent embargo will never expire.',
        widget=forms.CheckboxInput()
    )

    date_embargo = forms.DateField(
        required=False,
        label='Expiration date',
        help_text='Embargo duration are limited to a maximum of 30 days.',
        widget=forms.DateInput(
            attrs={
                'class': 'datepicker',
                'placeholder': 'Pick a date'
            }
        )
    )

    def clean_date_embargo(self):
        """Checks if date embargo is within 30 days"""
        date_embargo = self.cleaned_data['date_embargo']
        max_duration = date.today() + timedelta(30)
        if date_embargo and date_embargo > max_duration:
            error_msg = 'Embargo expiration date must be within 30 days of today'
            self._errors['date_embargo'] = self.error_class([error_msg])
        return date_embargo


class FOIANoteForm(forms.ModelForm):
    """A form for a FOIA Note"""

    class Meta:
        model = FOIANote
        fields = ['note']
        widgets = {'note': forms.Textarea(attrs={'class': 'prose-editor'})}


class FOIAAccessForm(forms.Form):
    """Form to add editors or viewers to a request."""
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=autocomplete_light.
        MultipleChoiceWidget('UserRequestSharingAutocomplete')
    )
    access_choices = [
        ('edit', 'Can Edit'),
        ('view', 'Can View'),
    ]
    access = forms.ChoiceField(choices=access_choices)

    def __init__(self, *args, **kwargs):
        required = kwargs.pop('required', True)
        super(FOIAAccessForm, self).__init__(*args, **kwargs)
        self.fields['users'].required = required
        self.fields['access'].required = required


class TrackingNumberForm(forms.ModelForm):
    """Form for adding a tracking number"""

    class Meta:
        model = TrackingNumber
        fields = ['tracking_id', 'reason']


class FOIAFlagForm(forms.Form):
    """Form for flagging a request"""
    prefix = 'flag'

    category = forms.ChoiceField(
        choices=[('', '-- Choose a category if one is relevant')] +
        PUBLIC_FLAG_CATEGORIES,
        required=False,
    )
    text = forms.CharField(widget=forms.Textarea, required=False)

    def clean(self):
        """Must fill in one of the fields"""
        cleaned_data = super(FOIAFlagForm, self).clean()
        if not cleaned_data.get('category') and not cleaned_data.get('text'):
            raise forms.ValidationError(
                'Must select a category or provide text'
            )


class FOIAContactUserForm(forms.Form):
    """Form for contacting the owner of a request"""
    prefix = 'contact'

    text = forms.CharField(widget=forms.Textarea)
