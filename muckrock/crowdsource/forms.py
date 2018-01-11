"""Forms for the crowdsource application"""

from django import forms

from muckrock.crowdsource.models import Crowdsource, CrowdsourceData


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


class CrowdsourceForm(forms.ModelForm):
    """Form for creating a crowdsource"""
    prefix = 'crowdsource'

    form_json = forms.CharField(
            widget=forms.HiddenInput(),
            )

    class Meta:
        model = Crowdsource
        fields = ('title', 'description')


CrowdsourceDataFormset = forms.inlineformset_factory(
        Crowdsource,
        CrowdsourceData,
        fields=('url',),
        extra=3,
        can_delete=False,
        )
