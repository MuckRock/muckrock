"""Forms for the crowdsource application"""

# Django
from django import forms
from django.contrib.auth.models import User
from django.core.validators import URLValidator

# Standard Library
import codecs
import csv
import json

# Third Party
from dal import forward

# MuckRock
from muckrock.communication.models import EmailAddress
from muckrock.core import autocomplete
from muckrock.crowdsource.constants import DOCUMENT_URL_RE, PROJECT_URL_RE
from muckrock.crowdsource.fields import FIELD_DICT
from muckrock.crowdsource.models import (
    Crowdsource,
    CrowdsourceData,
    CrowdsourceResponse,
)
from muckrock.crowdsource.tasks import datum_per_page, import_doccloud_proj
from muckrock.project.models import Project


class CrowdsourceAssignmentForm(forms.Form):
    """Generic crowdsource assignment form
    This is initialized with a crowdsource model which is used to dynamically
    populate the form
    """

    data_id = forms.IntegerField(widget=forms.HiddenInput, required=False)
    public = forms.BooleanField(
        label="Publicly credit you",
        help_text="When selected, we will note you contributed to the project and list "
        "your name next to responses marked public",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        crowdsource = kwargs.pop("crowdsource")
        user = kwargs.pop("user")
        super(CrowdsourceAssignmentForm, self).__init__(*args, **kwargs)

        for field in crowdsource.fields.filter(deleted=False):
            self.fields[str(field.pk)] = field.get_form_field()
        if user.is_anonymous and crowdsource.registration != "off":
            required = crowdsource.registration == "required"
            self.fields["full_name"] = forms.CharField(
                label="Full Name or Handle (Public)", required=required
            )
            self.fields["email"] = forms.EmailField(required=required)
            self.fields["newsletter"] = forms.BooleanField(
                initial=True,
                required=False,
                label="Get MuckRock's weekly newsletter with "
                "FOIA news, tips, and more",
            )
        if crowdsource.ask_public:
            # move public to the end
            self.fields["public"] = self.fields.pop("public")
        else:
            # remove public
            self.fields.pop("public")

    def clean_email(self):
        """Do a case insensitive uniqueness check"""
        email = self.cleaned_data["email"]
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "User with this email already exists. Please login first."
            )
        return email

    def clean(self):
        """Must supply both name and email, or neither"""
        data = super(CrowdsourceAssignmentForm, self).clean()

        if data.get("email") and not data.get("full_name"):
            self.add_error("full_name", "Name is required if registering with an email")
        if data.get("full_name") and not data.get("email"):
            self.add_error("email", "Email is required if registering with a name")


class CrowdsourceDataCsvForm(forms.Form):
    """Form for adding data to a crowdsource"""

    data_csv = forms.FileField(label="Data CSV File")
    doccloud_each_page = forms.BooleanField(
        label="Split Documents by Page",
        help_text="Each DocumentCloud URL will be split "
        "up into one assignment per page",
        required=False,
    )

    def clean_data_csv(self):
        """If there is a data CSV, ensure it has a URL column"""
        data_csv = self.cleaned_data["data_csv"]
        if data_csv:
            reader = csv.reader(codecs.iterdecode(data_csv, "utf-8"))
            headers = [h.lower() for h in next(reader)]
            if "url" not in headers:
                raise forms.ValidationError("Data CSV should contain a URL column")
            data_csv.seek(0)
        return data_csv

    def process_data_csv(self, crowdsource):
        """Create the crowdsource data from the uploaded CSV"""
        url_validator = URLValidator()
        data_csv = self.cleaned_data["data_csv"]
        doccloud_each_page = self.cleaned_data["doccloud_each_page"]
        if data_csv:
            reader = csv.reader(codecs.iterdecode(data_csv, "utf-8"))
            headers = [h.lower() for h in next(reader)]
            for line in reader:
                data = dict(list(zip(headers, line)))
                url = data.pop("url", "")
                doc_match = DOCUMENT_URL_RE.match(url)
                proj_match = PROJECT_URL_RE.match(url)
                if doccloud_each_page and doc_match:
                    datum_per_page.delay(
                        crowdsource.pk, doc_match.group("doc_id"), data
                    )
                elif proj_match:
                    import_doccloud_proj.delay(
                        crowdsource.pk,
                        proj_match.group("proj_id"),
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
                        crowdsource.data.create(url=url, metadata=data)


class CrowdsourceForm(forms.ModelForm, CrowdsourceDataCsvForm):
    """Form for creating a crowdsource"""

    prefix = "crowdsource"

    project = forms.ModelChoiceField(
        queryset=Project.objects.none(),
        required=False,
        widget=autocomplete.ModelSelect2(
            url="project-autocomplete",
            attrs={"data-placeholder": "Search projects"},
            forward=(forward.Const(True, "manager"),),
        ),
    )
    form_json = forms.CharField(widget=forms.HiddenInput(), initial="[]")
    submission_emails = forms.CharField(
        help_text="Comma seperated list of emails to send to on submission",
        required=False,
    )

    class Meta:
        model = Crowdsource
        fields = (
            "title",
            "project",
            "description",
            "data_limit",
            "user_limit",
            "registration",
            "form_json",
            "data_csv",
            "multiple_per_page",
            "project_only",
            "project_admin",
            "submission_emails",
            "ask_public",
        )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        super(CrowdsourceForm, self).__init__(*args, **kwargs)

        self.fields["data_csv"].required = False
        if not user.profile.is_advanced:
            del self.fields["registration"]
        self.fields["project"].queryset = Project.objects.get_manager(user)

    def clean_form_json(self):
        """Ensure the form JSON is in the correct format"""
        # pylint: disable=too-many-branches
        form_json = self.cleaned_data["form_json"]
        try:
            form_data = json.loads(form_json)
        except ValueError:
            raise forms.ValidationError("Invalid form data: Invalid JSON")
        if not isinstance(form_data, list):
            raise forms.ValidationError("Invalid form data: Not a list")
        if form_data == []:
            raise forms.ValidationError(
                "Having at least one field on the form is required"
            )
        for data in form_data:
            label = data.get("label")
            if not label:
                raise forms.ValidationError("Invalid form data: Missing label")
            required = data.get("required", False)
            if required not in [True, False]:
                raise forms.ValidationError("Invalid form data: Invalid required")
            type_ = data.get("type")
            if not type_:
                raise forms.ValidationError(
                    "Invalid form data: Missing type for {}".format(label)
                )
            if type_ not in FIELD_DICT:
                raise forms.ValidationError(
                    "Invalid form data: Bad type {}".format(type_)
                )
            field = FIELD_DICT[type_]
            if field.accepts_choices and "values" not in data:
                raise forms.ValidationError(
                    "Invalid form data: {} requires choices".format(type_)
                )
            if field.accepts_choices and "values" in data:
                for value in data["values"]:
                    choice_label = value.get("label")
                    if not choice_label:
                        raise forms.ValidationError(
                            "Invalid form data: Missing label for "
                            "choice of {}".format(label)
                        )
                    choice_value = value.get("value")
                    if not choice_value:
                        raise forms.ValidationError(
                            "Invalid form data: Missing value for "
                            "choice {} of {}".format(choice_label, label)
                        )
        return form_json

    def clean_submission_emails(self):
        """Validate the submission emails field"""
        return EmailAddress.objects.fetch_many(
            self.cleaned_data["submission_emails"], ignore_errors=False
        )


CrowdsourceDataFormsetBase = forms.inlineformset_factory(
    Crowdsource, CrowdsourceData, fields=("url",), extra=1, can_delete=False
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
                datum_per_page.delay(self.instance.pk, doc_match.group("doc_id"), {})
            elif proj_match:
                import_doccloud_proj.delay(
                    self.instance.pk,
                    proj_match.group("proj_id"),
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

    crowdsource = forms.ModelChoiceField(
        queryset=Crowdsource.objects.none(),
        required=False,
        widget=autocomplete.ModelSelect2(
            url="crowdsource-autocomplete",
            attrs={"data-placeholder": "Choose an unstarted crowdsource"},
        ),
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        super(CrowdsourceChoiceForm, self).__init__(*args, **kwargs)
        self.fields["crowdsource"].queryset = Crowdsource.objects.filter(
            status="draft", user=user
        )


class CrowdsourceMessageResponseForm(forms.Form):
    """Form to message the author of a response"""

    response = forms.ModelChoiceField(
        queryset=CrowdsourceResponse.objects.all(), widget=forms.HiddenInput()
    )
    subject = forms.CharField()
    body = forms.CharField(widget=forms.Textarea())
