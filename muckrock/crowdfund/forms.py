"""
Forms for Crowdfund application
"""

from django import forms

from muckrock.crowdfund.models import CrowdfundRequest

class CrowdfundRequestForm(forms.ModelForm):
    """Form to confirm enable crowdfunding on a FOIA"""

    class Meta:
        model = CrowdfundRequest
        fields = ('foia', 'name', 'description', 'payment_required', 'date_due')

