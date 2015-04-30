"""
Forms for Task app
"""

from django import forms

from muckrock.forms import MRFilterForm
from muckrock import foia

class TaskFilterForm(MRFilterForm):
    """Extends MRFilterForm with a 'show resolved' filter"""
    show_resolved = forms.BooleanField(
        label='Show Resolved'
    )

class ResponseTaskForm(forms.Form):
    move = forms.CharField()
    tracking_number = forms.CharField()
    status = forms.ChoiceField(choices=foia.models.STATUS)

    def clean_move(self):
        move_string = self.cleaned_data['move']
        move_list = move_string.split(',')
        for string in move_list:
            string.strip()
        return move_list
