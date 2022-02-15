"""
Forms for organization application
"""

# Django
from django import forms
from django.conf import settings

# MuckRock
from muckrock.organization.models import Organization


class OrganizationChoiceField(forms.ModelChoiceField):
    """Custom labels for organization choice field"""

    def label_from_instance(self, obj):
        """Change individual organization label to personal account"""
        return obj.display_name


class StripeForm(forms.Form):
    """Form for processing stripe payments"""

    stripe_token = forms.CharField(widget=forms.HiddenInput(), required=False)
    stripe_pk = forms.CharField(
        widget=forms.HiddenInput(), initial=settings.STRIPE_PUB_KEY
    )
    organization = OrganizationChoiceField(
        queryset=Organization.objects.none(),
        empty_label=None,
        label="Pay from which account",
    )
    use_card_on_file = forms.TypedChoiceField(
        label="Use Credit Card on File",
        coerce=lambda x: x == "True",
        initial=True,
        widget=forms.RadioSelect,
        choices=((True, "Card on File"), (False, "New Card")),
    )
    save_card = forms.BooleanField(label="Save credit card information", required=False)

    def __init__(self, *args, **kwargs):
        self._organization = kwargs.pop("organization", None)
        self._user = kwargs.pop("user")
        super(StripeForm, self).__init__(*args, **kwargs)

        # if auth user and org are given
        if self._user.is_authenticated and self._organization is not None:
            del self.fields["organization"]
            if self._organization.card:
                self.fields["use_card_on_file"].choices = (
                    (True, self._organization.card),
                    (False, "New Card"),
                )
            else:
                del self.fields["use_card_on_file"]
                self.fields["stripe_token"].required = True

        # if auth user but no org are given
        elif self._user.is_authenticated and self._organization is None:
            queryset = self._user.organizations.filter(
                memberships__admin=True
            ).order_by("-individual", "name")
            if len(queryset) == 1:
                self.fields["organization"].widget = forms.HiddenInput()
            self.fields["organization"].queryset = queryset
            # get the active org if you are an admin,
            # otherwise default to your individual org
            active_membership = self._user.memberships.filter(active=True, admin=True)
            self.fields["organization"].initial = (
                active_membership[0].organization
                if active_membership
                else self._user.profile.individual_organization
            )

        # if anonymous user is given
        elif not self._user.is_authenticated:
            del self.fields["organization"]
            del self.fields["use_card_on_file"]
            del self.fields["save_card"]

    def clean(self):
        """Validate using card on file and supplying new card"""
        data = super(StripeForm, self).clean()

        if data.get("use_card_on_file") and data.get("stripe_token"):
            self.add_error(
                "use_card_on_file",
                "You cannot use your card on file and enter a credit card number.",
            )

        if data.get("save_card") and not data.get("stripe_token"):
            self.add_error(
                "save_card",
                "You must enter credit card information in order to save it",
            )
        if data.get("save_card") and data.get("use_card_on_file"):
            self.add_error(
                "save_card",
                "You cannot save your card information if you are using your "
                "card on file.",
            )

        self._clean_card_required(data)

        return data

    def _clean_card_required(self, data):
        """Logic for checking if a payment is required
        May be overridden in subclasses
        """
        if (
            "use_card_on_file" in self.fields
            and not data.get("use_card_on_file")
            and not data.get("stripe_token")
        ):
            self.add_error(
                "use_card_on_file",
                "You must use your card on file or enter a credit card number.",
            )
