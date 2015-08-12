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
    """Simple form for acting on a ResponseTask"""
    move = forms.CharField(required=False)
    tracking_number = forms.CharField(required=False)
    price = forms.DecimalField(required=False)
    status = forms.ChoiceField(choices=foia.models.STATUS)

    def clean_move(self):
        """Splits a comma separated string into an array"""
        move_string = self.cleaned_data['move']
        if not move_string:
            return []
        move_list = move_string.split(',')
        for string in move_list:
            string = string.strip()
        return move_list
