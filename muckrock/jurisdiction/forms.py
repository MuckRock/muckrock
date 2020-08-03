"""Forms for Jurisdiction application"""

# Django
from django import forms

# MuckRock
from muckrock.foia.models import FOIARequest
from muckrock.jurisdiction.models import ExampleAppeal, Jurisdiction


class ExemptionSubmissionForm(forms.Form):
    """Allows exemptions to be submitted."""

    foia = forms.ModelChoiceField(queryset=FOIARequest.objects.all())
    language = forms.CharField(widget=forms.Textarea())


class FlagForm(forms.Form):
    """Form to flag an agency or jurisdiction"""

    reason = forms.CharField(
        widget=forms.Textarea(),
        label="Submit a Change",
        help_text=("Please describe the change in sufficient detail."),
    )


class AppealForm(forms.Form):
    """Appeals take a language input."""

    text = forms.CharField(widget=forms.Textarea())
    base_language = forms.ModelMultipleChoiceField(
        queryset=ExampleAppeal.objects.all(), required=False
    )


class CSVImportForm(forms.Form):
    """Import a CSV file of models"""

    csv_file = forms.FileField()
