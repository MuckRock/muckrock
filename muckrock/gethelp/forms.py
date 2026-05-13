"""Forms for the gethelp app"""

# Django
from django import forms


class GetHelpForm(forms.Form):
    text = forms.CharField(
        strip=True,
        error_messages={"required": "Please describe your issue."},
    )
    foia_pk = forms.IntegerField(required=False)
    category_label = forms.CharField(required=False)
    problem_title = forms.CharField(required=False)
