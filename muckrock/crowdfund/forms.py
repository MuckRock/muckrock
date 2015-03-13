"""
Forms for Crowdfund application
"""

from django import forms

from muckrock.crowdfund.models import CrowdfundRequest

class CrowdfundRequestForm(forms.Form):
    """Form to confirm enable crowdfunding on a FOIA"""
    name = forms.CharField()
    description = forms.CharField(widget=forms.Textarea())
    amount = forms.CharField()
    deadline = forms.CharField()
