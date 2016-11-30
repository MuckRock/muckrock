"""
Forms for Task app
"""

from django import forms

from muckrock.foia import STATUS

class FlaggedTaskForm(forms.Form):
    """Simple form for acting on a FlaggedTask"""
    text = forms.CharField(widget=forms.Textarea(attrs={
        'placeholder': 'Write your reply here'
    }))


class ProjectReviewTaskForm(forms.Form):
    """Simple form for acting on a FlaggedTask"""
    reply = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'placeholder': 'Write your reply here'
        }))

class StaleAgencyTaskForm(forms.Form):
    """Simple form for acting on a StaleAgencyTask"""
    email = forms.EmailField()


class ResponseTaskForm(forms.Form):
    """Simple form for acting on a ResponseTask"""
    move = forms.CharField(required=False)
    tracking_number = forms.CharField(required=False)
    price = forms.DecimalField(required=False)
    date_estimate = forms.DateField(
        label='Estimated completion date',
        required=False,
        widget=forms.DateInput(format='%m/%d/%Y', attrs={'placeholder': 'mm/dd/yyyy'}),
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
    status = forms.ChoiceField(choices=STATUS)
    set_foia = forms.BooleanField(label='Set request status', initial=True, required=False)
    proxy = forms.BooleanField(required=False, widget=forms.HiddenInput())

    def clean_move(self):
        """Splits a comma separated string into an array"""
        move_string = self.cleaned_data['move']
        if not move_string:
            return []
        move_list = move_string.split(',')
        for string in move_list:
            string = string.strip()
        return move_list
