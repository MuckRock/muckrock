"""
FOIA forms used on the detail page
"""

# Django
from django import forms
from django.contrib.auth.models import User

# Standard Library
from datetime import date, timedelta

# MuckRock
from muckrock.core import autocomplete
from muckrock.foia.models import END_STATUS, FOIANote, FOIARequest, TrackingNumber
from muckrock.organization.forms import StripeForm
from muckrock.task.constants import AGENCY_FLAG_CATEGORIES, PUBLIC_FLAG_CATEGORIES


class FOIAEstimatedCompletionDateForm(forms.ModelForm):
    """Form to change an estimaged completion date."""

    date_estimate = forms.DateField(
        label="Estimated completion date",
        help_text="The est. completion date is declared by the agency.",
        widget=forms.DateInput(format="%m/%d/%Y", attrs={"placeholder": "mm/dd/yyyy"}),
    )

    class Meta:
        model = FOIARequest
        fields = ["date_estimate"]


class FOIAEmbargoForm(forms.Form):
    """Form to configure an embargo on a request"""

    permanent_embargo = forms.BooleanField(
        required=False,
        label="Make permanent",
        help_text="A permanent embargo will never expire.",
        widget=forms.CheckboxInput(),
    )

    date_embargo = forms.DateField(
        required=False,
        label="Expiration date",
        help_text="Embargo duration are limited to a maximum of 30 days.",
        widget=forms.DateInput(
            attrs={"class": "datepicker", "placeholder": "Pick a date"}
        ),
    )

    def clean_date_embargo(self):
        """Checks if date embargo is within 30 days"""
        date_embargo = self.cleaned_data["date_embargo"]
        max_duration = date.today() + timedelta(30)
        if date_embargo and date_embargo > max_duration:
            error_msg = "Embargo expiration date must be within 30 days of today"
            self._errors["date_embargo"] = self.error_class([error_msg])
        return date_embargo


class FOIANoteForm(forms.ModelForm):
    """A form for a FOIA Note"""

    class Meta:
        model = FOIANote
        fields = ["note"]
        widgets = {"note": forms.Textarea(attrs={"class": "prose-editor"})}


class FOIAAccessForm(forms.Form):
    """Form to add editors or viewers to a request."""

    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(
            url="user-autocomplete", attrs={"data-placeholder": "User?"}
        ),
    )
    access_choices = [("edit", "Can Edit"), ("view", "Can View")]
    access = forms.ChoiceField(choices=access_choices)

    def __init__(self, *args, **kwargs):
        required = kwargs.pop("required", True)
        super().__init__(*args, **kwargs)
        self.fields["users"].required = required
        self.fields["access"].required = required


class FOIAOwnerForm(forms.Form):
    """Form to change the owner of a request"""

    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="user-autocomplete",
            attrs={"data-placeholder": "User?", "id": "id_owner"},
        ),
    )

    def __init__(self, *args, **kwargs):
        required = kwargs.pop("required", True)
        super().__init__(*args, **kwargs)
        self.fields["user"].required = required

    def change_owner(self, user, foias):
        """Perform the owner change"""
        foias = [f for f in foias if f.has_perm(user, "change")]
        new_user = self.cleaned_data["user"]
        for foia in foias:
            old_user = foia.composer.user
            foia.composer.user = new_user
            foia.composer.save()
            foia.notes.create(
                author=user,
                note=f"{user.username} ({user.pk}) changed ownership of this request "
                f"from {old_user.username} ({old_user.pk}) "
                f"to {new_user.username} ({new_user.pk})",
            )


class TrackingNumberForm(forms.ModelForm):
    """Form for adding a tracking number"""

    class Meta:
        model = TrackingNumber
        fields = ["tracking_id", "reason"]


class FOIAFlagForm(forms.Form):
    """Form for flagging a request"""

    prefix = "flag"

    category = forms.ChoiceField(
        choices=[("", "-- Choose a category if one is relevant")]
        + PUBLIC_FLAG_CATEGORIES,
        required=False,
    )
    text = forms.CharField(widget=forms.Textarea, required=False)

    def __init__(self, *args, **kwargs):
        is_agency_user = kwargs.pop("is_agency_user", False)
        all_choices = kwargs.pop("all_choices", False)
        super().__init__(*args, **kwargs)
        if is_agency_user:
            self.fields["category"].choices = [
                ("", "-- Choose a category if one is relevant")
            ] + AGENCY_FLAG_CATEGORIES
        if all_choices:
            self.fields["category"].choices = (
                [("", "-- Choose a category if one is relevant")]
                + AGENCY_FLAG_CATEGORIES
                + PUBLIC_FLAG_CATEGORIES
            )

    def clean(self):
        """Must fill in one of the fields"""
        cleaned_data = super(FOIAFlagForm, self).clean()
        if not cleaned_data.get("category") and not cleaned_data.get("text"):
            raise forms.ValidationError("Must select a category or provide text")


class FOIAContactUserForm(forms.Form):
    """Form for contacting the owner of a request"""

    prefix = "contact"

    text = forms.CharField(widget=forms.Textarea)


class FOIASoftDeleteForm(forms.Form):
    """Form to soft delete a request"""

    final_message = forms.CharField(
        widget=forms.Textarea,
        help_text="A final communication to the agency, explaining that the request is "
        "being withdrawn",
    )
    note = forms.CharField(
        widget=forms.Textarea,
        help_text="An internal note explaining why the request is being deleted",
    )

    def __init__(self, *args, **kwargs):
        foia = kwargs.pop("foia")
        super(FOIASoftDeleteForm, self).__init__(*args, **kwargs)
        if foia.status in END_STATUS:
            self.fields.pop("final_message")


class RequestFeeForm(StripeForm):
    """A form to pay request fees"""

    amount = forms.IntegerField(
        widget=forms.NumberInput(attrs={"class": "currency-field"}),
        min_value=0,
        help_text="We will add a 5% fee to this amount to cover our transaction fees.",
    )

    field_order = [
        "stripe_token",
        "stripe_pk",
        "amount",
        "organization",
        "use_card_on_file",
        "save_card",
    ]
