"""
Forms for Crowdfund application
"""

from django import forms

class CrowdfundEnableForm(forms.Form):
    """Form to confirm enable crowdfunding on a FOIA"""
    label = 'Enable crowdfunding on this FOIA request?'
    confirm = forms.BooleanField(label=label)
