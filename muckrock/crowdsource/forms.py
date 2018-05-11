"""Forms for the crowdsource application"""

# Django
from django import forms
from django.contrib.auth.models import User
from django.core.validators import URLValidator

# Standard Library
import json

# Third Party
import unicodecsv as csv
from autocomplete_light import shortcuts as autocomplete_light

# MuckRock
from muckrock.crowdsource.constants import DOCUMENT_URL_RE, PROJECT_URL_RE
from muckrock.crowdsource.fields import FIELD_DICT
from muckrock.crowdsource.models import Crowdsource, CrowdsourceData
from muckrock.crowdsource.tasks import datum_per_page, import_doccloud_proj


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
        user = kwargs.pop('user')
        super(CrowdsourceAssignmentForm, self).__init__(*args, **kwargs)

        for field in crowdsource.fields.all():
            self.fields[field.label] = field.get_form_field()
        if user.is_anonymous:
            self.fields['full_name'] = forms.CharField(
                label='Full Name or Handle (Public)'
            )
            self.fields['email'] = forms.EmailField()
            self.fields['newsletter'] = forms.BooleanField(
                initial=True,
                required=False,
                label='Get MuckRock\'s weekly newsletter with '
                'FOIA news, tips, and more',
            )

    def clean_email(self):
        """Do a case insensitive uniqueness check"""
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                'User with this email already exists. Please login first.'
            )
        return email


class CrowdsourceForm(forms.ModelForm):
    """Form for creating a crowdsource"""
    prefix = 'crowdsource'

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
        help_text='Each DocumentCloud URL will be split '
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
            'submission_email',
        )

    def clean_data_csv(self):
        """If there is a data CSV, ensure it has a URL column"""
        data_csv = self.cleaned_data['data_csv']
        if data_csv:
            reader = csv.reader(data_csv)
            headers = [h.lower() for h in next(reader)]
            if 'url' not in headers:
                raise forms.ValidationError(
                    'Data CSV should contain a URL column'
                )
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
                doc_match = DOCUMENT_URL_RE.match(url)
                proj_match = PROJECT_URL_RE.match(url)
                if doccloud_each_page and doc_match:
                    datum_per_page.delay(
                        crowdsource.pk,
                        doc_match.group('doc_id'),
                        data,
                    )
                elif proj_match:
                    import_doccloud_proj.delay(
                        crowdsource.pk,
                        proj_match.group('proj_id'),
                        data,
                        doccloud_each_page,
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
        # pylint: disable=too-many-branches
        form_json = self.cleaned_data['form_json']
        try:
            form_data = json.loads(form_json)
        except ValueError:
            raise forms.ValidationError('Invalid form data: Invalid JSON')
        if not isinstance(form_data, list):
            raise forms.ValidationError('Invalid form data: Not a list')
        if form_data == []:
            raise forms.ValidationError(
                'Having at least one field on the form is required'
            )
        for data in form_data:
            label = data.get('label')
            if not label:
                raise forms.ValidationError('Invalid form data: Missing label')
            required = data.get('required', False)
            if required not in [True, False]:
                raise forms.ValidationError(
                    'Invalid form data: Invalid required'
                )
            type_ = data.get('type')
            if not type_:
                raise forms.ValidationError(
                    'Invalid form data: Missing type for {}'.format(label)
                )
            if type_ not in FIELD_DICT:
                raise forms.ValidationError(
                    'Invalid form data: Bad type {}'.format(type_)
                )
            field = FIELD_DICT[type_]
            if field.accepts_choices and 'values' not in data:
                raise forms.ValidationError(
                    'Invalid form data: {} requires choices'.format(type_)
                )
            if field.accepts_choices and 'values' in data:
                for value in data['values']:
                    choice_label = value.get('label')
                    if not choice_label:
                        raise forms.ValidationError(
                            'Invalid form data: Missing label for '
                            'choice of {}'.format(label)
                        )
                    choice_value = value.get('value')
                    if not choice_value:
                        raise forms.ValidationError(
                            'Invalid form data: Missing value for '
                            'choice {} of {}'.format(choice_label, label)
                        )
        return form_json


CrowdsourceDataFormsetBase = forms.inlineformset_factory(
    Crowdsource,
    CrowdsourceData,
    fields=('url',),
    extra=1,
    can_delete=False,
)


class CrowdsourceDataFormset(CrowdsourceDataFormsetBase):
    """Crowdsource data formset"""

    def save(self, commit=True, doccloud_each_page=False):
        """Apply special cases to Document Cloud URLs"""
        instances = super(CrowdsourceDataFormset, self).save(commit=False)
        return_instances = []
        for instance in instances:
            doc_match = DOCUMENT_URL_RE.match(instance.url)
            proj_match = PROJECT_URL_RE.match(instance.url)
            if doccloud_each_page and doc_match:
                datum_per_page.delay(
                    self.instance.pk,
                    doc_match.group('doc_id'),
                    {},
                )
            elif proj_match:
                import_doccloud_proj.delay(
                    self.instance.pk,
                    proj_match.group('proj_id'),
                    {},
                    doccloud_each_page,
                )
            else:
                return_instances.append(instance)
                if commit:
                    instance.save()
        return return_instances


class CrowdsourceChoiceForm(forms.Form):
    """Form to choose a crowdsource"""
    crowdsource = autocomplete_light.ModelChoiceField(
        'CrowdsourceDraftAutocomplete',
        queryset=Crowdsource.objects.none(),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(CrowdsourceChoiceForm, self).__init__(*args, **kwargs)
        self.fields['crowdsource'].queryset = (
            Crowdsource.objects.filter(status='draft', user=user)
        )
