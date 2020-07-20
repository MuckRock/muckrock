"""
Forms for Tag application
"""

# Django
from django import forms

# Third Party
from dal import forward

# MuckRock
from muckrock.core import autocomplete
from muckrock.tags.models import Tag


class TagForm(forms.Form):
    """This form allows the selection of a tag"""

    tag_select = forms.ModelChoiceField(
        queryset=Tag.objects.all(),
        label=" ",
        required=False,
        widget=autocomplete.ModelSelect2(
            url="tag-autocomplete",
            attrs={"data-placeholder": "Search tags"},
            forward=(forward.Const(True, "slug"),),
        ),
    )
