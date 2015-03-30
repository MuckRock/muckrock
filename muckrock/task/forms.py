"""
Forms for Task app
"""

from django import forms
from django.contrib.auth.models import User

from muckrock.forms import MRFilterForm

class TaskFilterForm(MRFilterForm):
    """Extends MRFilterForm with a 'show resolved' filter"""
    show_resolved = forms.BooleanField(
        label='Show Resolved'
    )
