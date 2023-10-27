"""
Forms for FOIA Logs
"""

# Django
from django import forms
from django.contrib.auth.models import User

# MuckRock
from muckrock.agency.models import Agency
from muckrock.core import autocomplete
from muckrock.foia.models import FOIALog


class FOIALogUploadForm(forms.ModelForm):
    """A form to upload FOIA Log spreadsheet"""

    agency = forms.ModelChoiceField(
        queryset=Agency.objects.get_approved(),
        widget=autocomplete.ModelSelect2(
            url="agency-composer-autocomplete",
            attrs={"data-placeholder": "Search for agency"},
        ),
    )
    contributed_by = forms.ModelChoiceField(
        required=False,
        queryset=User.objects.filter(profile__agency=None),
        widget=autocomplete.ModelSelect2(
            url="user-autocomplete",
            attrs={"data-placeholder": "Search for user"},
        ),
    )
    start_date = forms.DateField(
        required=False,
        label="Start date",
        widget=forms.DateInput(
            attrs={"class": "datepicker", "placeholder": "Pick a date"}
        ),
    )
    end_date = forms.DateField(
        required=False,
        label="End date",
        widget=forms.DateInput(
            attrs={"class": "datepicker", "placeholder": "Pick a date"}
        ),
    )
    log = forms.FileField()

    class Meta:
        model = FOIALog
        fields = [
            "agency",
            "start_date",
            "end_date",
            "contributed_by",
            "internal_note",
            "source",
        ]
