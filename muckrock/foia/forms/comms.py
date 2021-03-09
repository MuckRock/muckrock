"""
FOIA forms for dealing with communications
"""

# Django
from django import forms
from django.contrib.auth.models import User

# Standard Library
from hmac import compare_digest

# Third Party
from phonenumber_field.formfields import PhoneNumberField

# MuckRock
from muckrock.communication.models import EmailAddress, PhoneNumber
from muckrock.core import autocomplete
from muckrock.core.fields import EmptyLastModelChoiceField
from muckrock.foia.models import FOIACommunication

AGENCY_STATUS = [
    ("processed", "Further Response Coming"),
    ("fix", "Fix Required"),
    ("payment", "Payment Required"),
    ("rejected", "Rejected"),
    ("no_docs", "No Responsive Documents"),
    ("done", "Completed"),
    ("partial", "Partially Completed"),
]


class FOIAAgencyReplyForm(forms.Form):
    """Form for direct agency reply"""

    status = forms.ChoiceField(
        label="What's the current status of the request?",
        choices=AGENCY_STATUS,
        help_text=" ",
    )
    tracking_id = forms.CharField(
        label="Tracking Number",
        help_text="If your agency assign a tracking number to the request, "
        "please enter it here.  We'll include this number in future "
        "followups if necessary",
        required=False,
    )
    date_estimate = forms.DateField(
        label="Estimated Completion Date",
        help_text="Enter the date you expect the request to be fufilled by.  "
        "We will not follow up with you until this date.",
        required=False,
    )
    price = forms.IntegerField(
        widget=forms.NumberInput(attrs={"class": "currency-field"}), required=False
    )
    reply = forms.CharField(label="Message to the requester", widget=forms.Textarea())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        """Make price required if status is set to payment"""
        cleaned_data = super(FOIAAgencyReplyForm, self).clean()
        status = cleaned_data.get("status")
        price = cleaned_data.get("price")

        if status == "payment" and price is None:
            self.add_error(
                "price",
                "You must set a price when setting the " "status to payment required",
            )
        return cleaned_data


class AgencyPasscodeForm(forms.Form):
    """A form for agencies to enter their passcode to view embargoed requests"""

    passcode = forms.CharField(
        label="Passcode",
        help_text="Please enter the passcode included with the original request",
        widget=forms.PasswordInput,
    )

    def __init__(self, *args, **kwargs):
        self.foia = kwargs.pop("foia")
        super().__init__(*args, **kwargs)

    def clean_passcode(self):
        """Compare the passcode"""
        if not compare_digest(self.cleaned_data["passcode"], self.foia.get_passcode()):
            raise forms.ValidationError("Incorrect passcode")
        return self.cleaned_data["passcode"]


class SendViaForm(forms.Form):
    """Form logic for specifying an address type to send to
    Should be subclassed"""

    via = forms.ChoiceField(
        choices=(
            ("portal", "Portal"),
            ("email", "Email"),
            ("fax", "Fax"),
            ("snail", "Snail Mail"),
        )
    )

    def __init__(self, *args, **kwargs):
        initial = kwargs.pop("initial", {})
        via = "snail"
        if self.foia:
            obj = self.foia
            agency = self.foia.agency
        elif hasattr(self, "agency") and self.agency:
            obj = self.agency
            agency = self.agency
        else:
            obj = None
            agency = None
        if obj:
            for addr in ("portal", "email", "fax"):
                if getattr(obj, addr):
                    via = addr
                    break
        initial.update({"via": via, "email": obj and obj.email, "fax": obj and obj.fax})
        super(SendViaForm, self).__init__(*args, initial=initial, **kwargs)
        # remove portal choice if the agency does not use a portal
        if agency and not agency.portal:
            self.fields["via"].choices = (
                ("email", "Email"),
                ("fax", "Fax"),
                ("snail", "Snail Mail"),
            )


class SendCommunicationForm(SendViaForm):
    """Form for sending individual communications"""

    email = forms.ModelChoiceField(
        queryset=EmailAddress.objects.filter(status="good"),
        required=False,
        widget=autocomplete.ModelSelect2(
            url="email-autocomplete",
            attrs={
                "data-placeholder": "Search for an email address",
                "data-html": False,
            },
        ),
    )
    fax = forms.ModelChoiceField(
        queryset=PhoneNumber.objects.filter(status="good", type="fax"),
        required=False,
        widget=autocomplete.ModelSelect2(
            url="fax-autocomplete",
            attrs={"data-placeholder": "Search for a fax number", "data-html": False},
        ),
    )

    def __init__(self, *args, **kwargs):
        super(SendCommunicationForm, self).__init__(*args, **kwargs)
        # create auto complete fields for creating new instances
        # these are created here since they have invalid identifier names
        # only add them if the field is bound, as we do not want to add them
        # to the form display, but do want to use them to process incoming data
        if self.is_bound:
            self.fields["email-autocomplete"] = forms.CharField(
                widget=forms.HiddenInput(), required=False
            )
            self.fields["fax-autocomplete"] = forms.CharField(
                widget=forms.HiddenInput(), required=False
            )

    def clean(self):
        """Ensure the selected method is ok for this foia and the correct
        corresponding information is provided"""

        cleaned_data = super(SendCommunicationForm, self).clean()
        if cleaned_data.get("via") == "email" and not cleaned_data.get("email"):
            self.add_error("email", "An email address is required if sending via email")
        elif cleaned_data.get("via") == "fax" and not cleaned_data.get("fax"):
            self.add_error("fax", "A fax number is required if sending via fax")
        return cleaned_data


class FOIAAdminFixForm(SendCommunicationForm):
    """Form with extra options for staff to follow up to requests"""

    from_user = forms.ModelChoiceField(label="From", queryset=User.objects.none())
    other_emails = forms.ModelMultipleChoiceField(
        label="CC",
        queryset=EmailAddress.objects.filter(status="good"),
        required=False,
        widget=autocomplete.ModelSelect2Multiple(
            url="email-autocomplete",
            attrs={
                "data-placeholder": "Search for an email address",
                "data-html": False,
            },
        ),
    )
    subject = forms.CharField(max_length=255)
    comm = forms.CharField(label="Body", widget=forms.Textarea())

    field_order = [
        "from_user",
        "via",
        "email",
        "other_emails",
        "fax",
        "subject",
        "comm",
    ]

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request")
        self.foia = kwargs.pop("foia")
        super(FOIAAdminFixForm, self).__init__(*args, **kwargs)
        muckrock_staff = User.objects.get(username="MuckrockStaff")
        self.fields["from_user"].queryset = User.objects.filter(
            pk__in=[muckrock_staff.pk, request.user.pk, self.foia.user.pk]
        )
        self.fields["from_user"].initial = request.user.pk


class ResendForm(SendCommunicationForm):
    """A form for resending a communication"""

    communication = forms.ModelChoiceField(
        queryset=FOIACommunication.objects.all(), widget=forms.HiddenInput()
    )

    def __init__(self, *args, **kwargs):
        # set initial data based on the communication
        comm = kwargs.pop("communication", None)
        if comm:
            self.foia = comm.foia
        else:
            self.foia = None
        initial = kwargs.pop("initial", {})
        initial.update({"communication": comm})
        super(ResendForm, self).__init__(*args, initial=initial, **kwargs)
        self.fields["via"].widget.attrs.update({"class": "resend-via"})
        self.fields["email"].widget.attrs.update({"class": "resend-email"})
        self.fields["fax"].widget.attrs.update({"class": "resend-fax"})

    def clean(self):
        """Set self.foia during cleaning"""
        if "communication" in self.cleaned_data:
            self.foia = self.cleaned_data["communication"].foia
        return super(ResendForm, self).clean()


class ContactInfoForm(SendViaForm):
    """A form to let advanced users control where the communication will be sent"""

    email = EmptyLastModelChoiceField(
        queryset=EmailAddress.objects.none(), required=False, empty_label="Other..."
    )
    other_email = forms.EmailField(required=False)
    fax = EmptyLastModelChoiceField(
        queryset=PhoneNumber.objects.none(), required=False, empty_label="Other..."
    )
    other_fax = PhoneNumberField(required=False)
    use_contact_information = forms.BooleanField(
        widget=forms.HiddenInput(), initial=False, required=False
    )

    def __init__(self, *args, **kwargs):
        self.foia = kwargs.pop("foia", None)
        self.agency = kwargs.pop("agency", None)
        appeal = kwargs.pop("appeal", False)
        super(ContactInfoForm, self).__init__(*args, **kwargs)
        self.fields["via"].required = False
        # add class we can reference from javascript
        for field in self.fields:
            self.fields[field].widget.attrs["class"] = field
        if self.agency:
            agency = self.agency
        elif self.foia:
            agency = self.foia.agency.appeal_agency if appeal else self.foia.agency
        else:
            agency = None
        if agency:
            self.fields["email"].queryset = (
                agency.emails.filter(status="good")
                .exclude(email__endswith="muckrock.com")
                .distinct()
            )
            self.fields["fax"].queryset = agency.phones.filter(
                status="good", type="fax"
            ).distinct()

    def clean(self):
        """Make other fields required if chosen"""
        cleaned_data = super(ContactInfoForm, self).clean()
        if not cleaned_data.get("use_contact_information"):
            return cleaned_data
        if not cleaned_data.get("via"):
            self.add_error("via", "This field is required")
        if (
            cleaned_data.get("via") == "email"
            and not cleaned_data.get("email")
            and not cleaned_data.get("other_email")
        ):
            self.add_error("other_email", "Please enter an email address")
        if (
            cleaned_data.get("via") == "fax"
            and not cleaned_data.get("fax")
            and not cleaned_data.get("other_fax")
        ):
            self.add_error("other_fax", "Please enter a fax number")
        return cleaned_data

    def clean_email(self):
        """Turn email model into a string for serializing"""
        if self.cleaned_data["email"]:
            return self.cleaned_data["email"].email
        else:
            return self.cleaned_data["email"]

    def clean_fax(self):
        """Turn phone number model into a string for serializing"""
        if self.cleaned_data["fax"]:
            return self.cleaned_data["fax"].number.as_international
        else:
            return self.cleaned_data["fax"]
