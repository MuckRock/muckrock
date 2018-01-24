"""Forms for the crowdsource application"""

from django import forms
from django.core.validators import URLValidator

from autocomplete_light import shortcuts as autocomplete_light
import json
import re
import unicodecsv as csv

from muckrock.crowdsource.models import Crowdsource, CrowdsourceData
from muckrock.crowdsource.fields import FIELD_DICT
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

    project = autocomplete_light.ModelChoiceField(
            'ProjectManagerAutocomplete',
            required=False,
            )
    form_json = forms.CharField(
            widget=forms.HiddenInput(),
            initial='[]',
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
                'project',
                'description',
                'data_limit',
                'user_limit',
                'form_json',
                'data_csv',
                'multiple_per_page',
                'project_only',
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
        url_validator = URLValidator()
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
                    # skip invalid URLs
                    try:
                        url_validator(url)
                    except forms.ValidationError:
                        pass
                    else:
                        crowdsource.data.create(
                                url=url,
                                metadata=data,
                                )

    def clean_form_json(self):
        """Ensure the form JSON is in the correct format"""
        form_json = self.cleaned_data['form_json']
        try:
            form_data = json.loads(form_json)
        except ValueError:
            raise forms.ValidationError('Invalid form data: Invalid JSON')
        if not isinstance(form_data, list):
            raise forms.ValidationError('Invalid form data: Not a list')
        if form_data == []:
            raise forms.ValidationError(
                    'Having at least one field on the form is required')
        for data in form_data:
            label = data.get('label')
            if not label:
                raise forms.ValidationError('Invalid form data: Missing label')
            type_ = data.get('type')
            if not type_:
                raise forms.ValidationError(
                        'Invalid form data: Missing type for {}'.format(label))
            if type_ not in FIELD_DICT:
                raise forms.ValidationError(
                        'Invalid form data: Bad type {}'.format(type_))
            field = FIELD_DICT[type_]
            if field.accepts_choices and 'values' not in data:
                raise forms.ValidationError(
                        'Invalid form data: {} requires choices'.format(type_))
            if field.accepts_choices and 'values' in data:
                for value in data['values']:
                    choice_label = value.get('label')
                    if not choice_label:
                        raise forms.ValidationError(
                                'Invalid form data: Missing label for '
                                'choice of {}'.format(label))
                    choice_value = value.get('value')
                    if not choice_value:
                        raise forms.ValidationError(
                                'Invalid form data: Missing value for '
                                'choice {} of {}'.format(choice_label, label))
        return form_json


CrowdsourceDataFormset = forms.inlineformset_factory(
        Crowdsource,
        CrowdsourceData,
        fields=('url',),
        extra=1,
        can_delete=False,
        )
