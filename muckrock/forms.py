"""
Forms for MuckRock
"""

from django import forms
from django.contrib.auth.models import User

from autocomplete_light import shortcuts as autocomplete_light
from autocomplete_light.contrib.taggit_field import TaggitField
from autocomplete_light.widgets import TextWidget
import six
from taggit.utils import edit_string_for_tags

from muckrock.agency.models import Agency
from muckrock.jurisdiction.models import Jurisdiction

class TaggitWidget(TextWidget):
    """built in one breaks on select_related... not sure why"""
    def render(self, name, value, attrs=None):
        if value is not None and not isinstance(value, six.string_types):
            value = edit_string_for_tags(
                [o.tag for o in value])
        return super(TaggitWidget, self).render(name, value, attrs)


class MRFilterForm(forms.Form):
    """A generic class to filter a list of items"""
    user = forms.ModelChoiceField(
        required=False,
        queryset=User.objects.all(),
        widget=autocomplete_light.ChoiceWidget(
            'UserAutocomplete',
            attrs={'placeholder': 'All Users'}))
    agency = forms.ModelChoiceField(
        required=False,
        queryset=Agency.objects.all(),
        widget=autocomplete_light.ChoiceWidget(
            'AgencyAutocomplete',
            attrs={'placeholder': 'All Agencies'}))
    jurisdiction = forms.ModelChoiceField(
        required=False,
        queryset=Jurisdiction.objects.all(),
        widget=autocomplete_light.ChoiceWidget(
            'JurisdictionAutocomplete',
            attrs={'placeholder': 'All Jurisdictions'}))
    tags = TaggitField(widget=TaggitWidget(
        'TagAutocomplete',
        attrs={
            'placeholder': 'All Tags (comma separated)',
            'data-autocomplete-minimum-characters': 1}))


class TagManagerForm(forms.Form):
    """A form with an autocomplete input for tags"""
    tags = TaggitField(widget=TaggitWidget(
        'TagAutocomplete',
        attrs={
            'placeholder': 'Tags',
            'data-autocomplete-minimum-characters': 1}))

class NewsletterSignupForm(forms.Form):
    """A form for adding an email to a MailChimp mailing list."""
    email = forms.EmailField()
    list = forms.CharField(widget=forms.HiddenInput)
