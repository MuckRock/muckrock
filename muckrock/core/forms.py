"""
Forms for MuckRock
"""

# Django
from django import forms
from django.conf import settings
from django.contrib.auth.models import User

# Third Party
import six
from autocomplete_light import shortcuts as autocomplete_light
from autocomplete_light.contrib.taggit_field import TaggitField
from autocomplete_light.widgets import TextWidget
from taggit.utils import edit_string_for_tags

# MuckRock
from muckrock.agency.models import Agency
from muckrock.jurisdiction.models import Jurisdiction


class TaggitWidget(TextWidget):
    """built in one breaks on select_related... not sure why"""

    def render(self, name, value, attrs=None):
        if value is not None and not isinstance(value, six.string_types):
            value = edit_string_for_tags(value)
        return super(TaggitWidget, self).render(name, value, attrs)


class MRFilterForm(forms.Form):
    """A generic class to filter a list of items"""
    user = forms.ModelChoiceField(
        required=False,
        queryset=User.objects.all(),
        widget=autocomplete_light.ChoiceWidget(
            'UserAutocomplete', attrs={
                'placeholder': 'All Users'
            }
        )
    )
    agency = forms.ModelChoiceField(
        required=False,
        queryset=Agency.objects.all(),
        widget=autocomplete_light.ChoiceWidget(
            'AgencyAutocomplete', attrs={
                'placeholder': 'All Agencies'
            }
        )
    )
    jurisdiction = forms.ModelChoiceField(
        required=False,
        queryset=Jurisdiction.objects.all(),
        widget=autocomplete_light.ChoiceWidget(
            'JurisdictionAutocomplete',
            attrs={
                'placeholder': 'All Jurisdictions'
            }
        )
    )
    tags = TaggitField(
        widget=TaggitWidget(
            'TagAutocomplete',
            attrs={
                'placeholder': 'All Tags (comma separated)',
                'data-autocomplete-minimum-characters': 1
            }
        )
    )


class TagManagerForm(forms.Form):
    """A form with an autocomplete input for tags"""
    tags = TaggitField(
        widget=TaggitWidget(
            'TagAutocomplete',
            attrs={
                'placeholder': 'Tags',
                'data-autocomplete-minimum-characters': 1
            }
        )
    )

    def __init__(self, *args, **kwargs):
        required = kwargs.pop('required', True)
        super(TagManagerForm, self).__init__(*args, **kwargs)
        self.fields['tags'].required = required


class NewsletterSignupForm(forms.Form):
    """A form for adding an email to a MailChimp mailing list."""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'email address'
        })
    )
    list = forms.CharField(widget=forms.HiddenInput)
    default = forms.BooleanField(initial=True, required=False)


class SearchForm(forms.Form):
    """A form for searching a single model."""
    # pylint: disable=invalid-name
    q = forms.CharField(
        required=False,
        label='Search',
        widget=forms.TextInput(attrs={
            'type': 'search',
        })
    )


class StripeForm(forms.Form):
    """A form to collect a stripe token for a given amount and email."""
    # remove after crowdunds and donations moved to stripe
    stripe_pk = forms.CharField(
        initial=settings.STRIPE_PUB_KEY,
        required=False,
        widget=forms.HiddenInput
    )
    stripe_token = forms.CharField(
        widget=forms.HiddenInput(attrs={
            'autocomplete': 'off'
        })
    )
    stripe_email = forms.EmailField(widget=forms.HiddenInput)
    stripe_fee = forms.IntegerField(
        initial=0, required=False, widget=forms.HiddenInput
    )
    stripe_label = forms.CharField(
        initial='Buy', required=False, widget=forms.HiddenInput
    )
    stripe_description = forms.CharField(
        required=False, widget=forms.HiddenInput
    )
    stripe_bitcoin = forms.BooleanField(
        initial=True, required=False, widget=forms.HiddenInput
    )
    stripe_amount = forms.IntegerField(min_value=0)
    type = forms.ChoiceField(
        choices=(
            ('one-time', 'One Time'),
            ('monthly', 'Monthly'),
        )
    )
