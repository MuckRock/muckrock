"""
Forms for Tag application
"""

from django import forms

from autocomplete_light import shortcuts as autocomplete_light


class TagForm(forms.Form):
    """This form allows the selection of a tag"""

    tag_select = autocomplete_light.ModelChoiceField(
        'TagSlugAutocomplete',
        label=' ',
        required=False,
    )
