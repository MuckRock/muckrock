"""Forms for Agency application"""

# Django
from django import forms

# Third Party
from localflavor.us.forms import USZipCodeField
from localflavor.us.us_states import STATE_CHOICES
from phonenumber_field.formfields import PhoneNumberField

# MuckRock
from muckrock.agency.models import Agency, AgencyAddress, AgencyEmail, AgencyPhone
from muckrock.communication.models import Address, EmailAddress, PhoneNumber
from muckrock.core import autocomplete
from muckrock.core.fields import FullEmailField
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.portal.models import PORTAL_TYPES, Portal


class AgencyForm(forms.ModelForm):
    """A form for an Agency"""

    jurisdiction = forms.ModelChoiceField(
        queryset=Jurisdiction.objects.filter(hidden=False),
        widget=autocomplete.ModelSelect2(
            url="jurisdiction-autocomplete",
            attrs={"data-placeholder": "Search for jurisdiction"},
        ),
    )
    mail_name = forms.CharField(
        required=False,
        max_length=40,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Mail To (Can be agency name, shortened to fit "
                "into 40 characters)"
            }
        ),
    )
    address_suite = forms.CharField(
        required=False,
        max_length=64,
        widget=forms.TextInput(
            attrs={"placeholder": "Suite / Building Number (Optional)"}
        ),
    )
    address_street = forms.CharField(
        required=False,
        max_length=64,
        widget=forms.TextInput(attrs={"placeholder": "Street"}),
    )
    address_city = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={"placeholder": "City"}),
    )
    address_state = forms.ChoiceField(
        required=False, choices=(("", "---"),) + tuple(STATE_CHOICES)
    )
    address_zip = USZipCodeField(
        required=False, widget=forms.TextInput(attrs={"placeholder": "Zip"})
    )
    email = FullEmailField(required=False)
    website = forms.URLField(label="General Website", required=False)
    phone = PhoneNumberField(required=False)
    fax = PhoneNumberField(required=False)
    portal_url = forms.URLField(
        required=False,
        help_text="This is a URL where you can submit a request directly from "
        "the website.  You should probably leave this blank unless you know "
        "this is what you want",
    )

    portal_type = forms.ChoiceField(choices=PORTAL_TYPES, initial="other")

    def save(self, *args, **kwargs):
        """Save email, phone, fax, and address models on save"""
        # pylint: disable=signature-differs
        agency = super(AgencyForm, self).save(*args, **kwargs)
        if self.cleaned_data["email"]:
            email_address = EmailAddress.objects.fetch(self.cleaned_data["email"])
            AgencyEmail.objects.create(
                agency=agency,
                email=email_address,
                request_type="primary",
                email_type="to",
            )
        if self.cleaned_data["phone"]:
            phone_number, _ = PhoneNumber.objects.update_or_create(
                number=self.cleaned_data["phone"], defaults={"type": "phone"}
            )
            AgencyPhone.objects.create(agency=agency, phone=phone_number)
        if self.cleaned_data["fax"]:
            fax_number, _ = PhoneNumber.objects.update_or_create(
                number=self.cleaned_data["fax"], defaults={"type": "fax"}
            )
            AgencyPhone.objects.create(
                agency=agency, phone=fax_number, request_type="primary"
            )
        if (
            self.cleaned_data["address_suite"]
            or self.cleaned_data["address_street"]
            or self.cleaned_data["address_city"]
            or self.cleaned_data["address_state"]
            or self.cleaned_data["address_zip"]
        ):
            address, _ = Address.objects.get_or_create(
                suite=self.cleaned_data["address_suite"],
                street=self.cleaned_data["address_street"],
                city=self.cleaned_data["address_city"],
                state=self.cleaned_data["address_state"],
                zip_code=self.cleaned_data["address_zip"],
                agency_override="",
                attn_override="",
                address="",
            )
            # clear out any previously set primary addresses
            AgencyAddress.objects.filter(agency=agency, request_type="primary").delete()
            AgencyAddress.objects.create(
                agency=agency, address=address, request_type="primary"
            )
        if self.cleaned_data["portal_url"]:
            portal_type = self.cleaned_data["portal_type"]
            portal, _ = Portal.objects.get_or_create(
                url=self.cleaned_data["portal_url"],
                defaults={
                    "type": portal_type,
                    "name": "%s %s" % (agency, dict(PORTAL_TYPES)[portal_type]),
                },
            )
            agency.portal = portal
            agency.save()

    def get_fields(self):
        """Get the fields for rendering"""
        field_order = [
            "name",
            "jurisdiction",
            "aliases",
            "address",
            "email",
            "url",
            "website",
            "phone",
            "fax",
            "portal_url",
            "portal_type",
        ]
        return [field if field == "address" else self[field] for field in field_order]

    class Meta:
        model = Agency
        fields = [
            "name",
            "mail_name",
            "jurisdiction",
            "aliases",
            "email",
            "url",
            "website",
            "phone",
            "fax",
            "portal_url",
            "portal_type",
        ]
        labels = {"aliases": "Alias", "url": "FOIA or public information contact page"}
        help_texts = {
            "aliases": "An alternate name for the agency, "
            'e.g. "CIA" is an alias for "Central Intelligence Agency".'
        }


class AgencyMergeForm(forms.Form):
    """A form to merge two agencies"""

    good_agency = forms.ModelChoiceField(
        queryset=Agency.objects.get_approved(),
        widget=autocomplete.ModelSelect2(
            url="agency-composer-autocomplete",
            attrs={"data-placeholder": "Search for agency"},
        ),
    )
    bad_agency = forms.ModelChoiceField(
        queryset=Agency.objects.get_approved(),
        widget=autocomplete.ModelSelect2(
            url="agency-composer-autocomplete",
            attrs={"data-placeholder": "Search for agency"},
        ),
    )
    confirmed = forms.BooleanField(
        initial=False, widget=forms.HiddenInput(), required=False
    )

    def __init__(self, *args, **kwargs):
        confirmed = kwargs.pop("confirmed", False)
        super(AgencyMergeForm, self).__init__(*args, **kwargs)
        if confirmed:
            self.fields["confirmed"].initial = True
            self.fields["good_agency"].widget = forms.HiddenInput()
            self.fields["bad_agency"].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super(AgencyMergeForm, self).clean()
        good_agency = cleaned_data.get("good_agency")
        bad_agency = cleaned_data.get("bad_agency")
        if good_agency and good_agency == bad_agency:
            raise forms.ValidationError("Cannot merge an agency into itself")
        return cleaned_data


class AgencyMassImportForm(forms.Form):
    """Import a CSV file of models"""

    csv = forms.FileField()
    match_or_import = forms.ChoiceField(
        required=True,
        choices=(("match", "Match"), ("import", "Import"),),
        help_text="Match will just match the jurisdiction and agency without "
        "changing anything.  Import will create unmatched agencies and set or "
        "update supplied contact information",
    )
    email = forms.BooleanField(
        required=False,
        help_text="Checking this will run the import in the background and "
        "email you the results when finished.  This will allow for large imports.",
    )
    dry_run = forms.BooleanField(
        required=False,
        help_text="Checking this will run an import, but not save any of the "
        "changes to the database",
    )
