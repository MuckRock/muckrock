"""
Forms for Tag application
"""

# Django
from django import forms

# Third Party
from autocomplete_light import shortcuts as autocomplete_light


class TagForm(forms.Form):
    """This form allows the selection of a tag"""

    tag_select = autocomplete_light.ModelChoiceField(
        'TagSlugAutocomplete',
        label=' ',
        required=False,
    )
