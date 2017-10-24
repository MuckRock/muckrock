"""
Forms for Task app
"""

from django import forms

from autocomplete_light import shortcuts as autocomplete_light

from muckrock.communication.utils import get_email_or_fax
from muckrock.foia.models import STATUS


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


class ReviewAgencyTaskForm(forms.Form):
    """Simple form to allow selecting an email address or fax number"""
    email_or_fax = forms.CharField(
            label='Update email or fax on checked requests:',
            widget=autocomplete_light.TextWidget('EmailOrFaxAutocomplete'),
            required=False,
            )
    update_agency_info = forms.BooleanField(
            label='Update agency\'s main contact info?',
            required=False,
            )
    snail_mail = forms.BooleanField(
            label='Make snail mail the prefered communication method',
            required=False,
            )
    reply = forms.CharField(
            label='Reply:',
            widget=forms.Textarea(
                attrs={
                    'rows': 5,
                    }),
            )

    def clean_email_or_fax(self):
        """Validate the email_or_fax field"""
        if self.cleaned_data['email_or_fax']:
            return get_email_or_fax(self.cleaned_data['email_or_fax'])
        else:
            return None

    def clean(self):
        """Make email_or_fax required if snail mail is not checked"""
        cleaned_data = super(ReviewAgencyTaskForm, self).clean()
        email_or_fax = cleaned_data.get('email_or_fax')
        snail_mail = cleaned_data.get('snail_mail')

        if not email_or_fax and not snail_mail:
            self.add_error(
                    'email_or_fax',
                    'Required if snail mail is not checked',
                    )


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
