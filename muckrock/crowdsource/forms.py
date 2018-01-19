"""Forms for the crowdsource application"""

from django import forms

import re
import unicodecsv as csv

from muckrock.crowdsource.models import Crowdsource, CrowdsourceData
from muckrock.crowdsource.tasks import datum_per_page


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
    document_url_re = re.compile(
            r'https?://www[.]documentcloud[.]org/documents/'
            r'(?P<doc_id>[0-9A-Za-z-]+)[.]html'
            )

    form_json = forms.CharField(
            widget=forms.HiddenInput(),
            )
    data_csv = forms.FileField(
            label='Data CSV File',
            required=False,
            )
    doccloud_each_page = forms.BooleanField(
            label='Split Documents by Page',
            help_text='Each DocumentCloud URL in the data CSV will be split '
            'up into one assignment per page',
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
        doccloud_each_page = self.cleaned_data['doccloud_each_page']
        if data_csv:
            reader = csv.reader(data_csv)
            headers = [h.lower() for h in next(reader)]
            for line in reader:
                data = dict(zip(headers, line))
                url = data.pop('url', '')
                match = self.document_url_re.match(url)
                if doccloud_each_page and match:
                    datum_per_page.delay(
                            crowdsource.pk,
                            match.group('doc_id'),
                            data,
                            )
                elif url:
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
