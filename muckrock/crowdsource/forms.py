"""Forms for the crowdsource application"""

from django import forms


class CrowdsourceAssignmentForm(forms.Form):
    """Generic crowdsource assignment form
    This is initialized with a crowdsource model which is used to dynamically
    populate the form
    """

    data_id = forms.IntegerField(
            widget=forms.HiddenInput,
            required=False,
            )

    def __init__(self, *args, **kwargs):
        crowdsource = kwargs.pop('crowdsource')
        super(CrowdsourceAssignmentForm, self).__init__(*args, **kwargs)

        for field in crowdsource.fields.all():
            self.fields[field.label] = field.get_form_field()
