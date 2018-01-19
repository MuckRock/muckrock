"""Forms for the crowdsource application"""

from django import forms

import unicodecsv as csv

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
    data_csv = forms.FileField(
            label='Data CSV File',
            required=False,
            )

    class Meta:
        model = Crowdsource
        fields = (
                'title',
                'description',
                'data_limit',
                'user_limit',
                'form_json',
                'data_csv',
                )

    def clean_data_csv(self):
        """If there is a data CSV, ensure it has a URL column"""
        data_csv = self.cleaned_data['data_csv']
        if data_csv:
            reader = csv.reader(data_csv)
            headers = [h.lower() for h in next(reader)]
            if 'url' not in headers:
                raise forms.ValidationError('Data CSV should contain a URL column')
            data_csv.seek(0)
        return data_csv

    def process_data_csv(self, crowdsource):
        """Create the crowdsource data from the uploaded CSV"""
        data_csv = self.cleaned_data['data_csv']
        if data_csv:
            reader = csv.reader(data_csv)
            headers = [h.lower() for h in next(reader)]
            for line in reader:
                data = dict(zip(headers, line))
                url = data.pop('url', '')
                if url:
                    crowdsource.data.create(
                            url=url,
                            metadata=data,
                            )


CrowdsourceDataFormset = forms.inlineformset_factory(
        Crowdsource,
        CrowdsourceData,
        fields=('url',),
        extra=1,
        can_delete=False,
        )
