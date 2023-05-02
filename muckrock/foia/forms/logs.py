"""
Forms for FOIA Logs
"""

# Django
from django import forms

# MuckRock
from muckrock.agency.models import Agency
from muckrock.core import autocomplete


class FOIALogUploadForm(forms.Form):
    """A form to upload FOIA Log spreadsheet"""

    agency = forms.ModelChoiceField(
        queryset=Agency.objects.get_approved(),
        widget=autocomplete.ModelSelect2(
            url="agency-composer-autocomplete",
            attrs={"data-placeholder": "Search for agency"},
        ),
    )
    log = forms.FileField()
