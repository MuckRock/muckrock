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
    date_estimate = forms.DateField(
        label='Estimated completion date',
        widget=forms.DateInput(format='%m/%d/%Y'),
        input_formats=[
            '%Y-%m-%d',      # '2006-10-25'
            '%m/%d/%Y',      # '10/25/2006'
            '%m/%d/%y',      # '10/25/06'
            '%b %d %Y',      # 'Oct 25 2006'
            '%b %d, %Y',     # 'Oct 25, 2006'
            '%d %b %Y',      # '25 Oct 2006'
            '%d %b, %Y',     # '25 Oct, 2006'
            '%B %d %Y',      # 'October 25 2006'
            '%B %d, %Y',     # 'October 25, 2006'
            '%d %B %Y',      # '25 October 2006'
            '%d %B, %Y']     # '25 October, 2006'
    )
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
