"""
Forms for MuckRock
"""

# Django
from django import forms
from django.conf import settings
from django.utils import formats

# Standard Library
from datetime import date, datetime

# Third Party
from dal.autocomplete import TaggitSelect2
from phonenumber_field.formfields import PhoneNumberField
from taggit.forms import TagField


class NativeDateInput(forms.DateInput):
    """
    The browser's own date picker.

    `min` and `max` attrs may be dates or callables returning dates, resolved
    at render time. The browser refuses to submit a date outside them.
    """

    input_type = "date"

    def __init__(self, attrs=None):
        # Date inputs only accept ISO values, whatever the user's locale shows.
        super().__init__(attrs, format="%Y-%m-%d")

    def format_value(self, value):
        # Filter URLs bookmarked before this widget carry MM/DD/YYYY dates.
        if isinstance(value, str):
            for input_format in formats.get_format("DATE_INPUT_FORMATS"):
                try:
                    value = datetime.strptime(value, input_format).date()
                    break
                except ValueError:
                    continue
        return super().format_value(value)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        widget_attrs = context["widget"]["attrs"]
        for key in ("min", "max"):
            bound = widget_attrs.get(key)
            if callable(bound):
                bound = bound()
            if isinstance(bound, date):
                widget_attrs[key] = bound.isoformat()
        return context


class TagManagerForm(forms.Form):
    """A form with an autocomplete input for tags"""

    tags = TagField(
        widget=TaggitSelect2(url="tag-autocomplete", attrs={"data-placeholder": "Tags"})
    )

    def __init__(self, *args, **kwargs):
        required = kwargs.pop("required", True)
        super().__init__(*args, **kwargs)
        self.fields["tags"].required = required


class NewsletterSignupForm(forms.Form):
    """A form for adding an email to a MailChimp mailing list."""

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"placeholder": "Your email address"})
    )
    list = forms.CharField(widget=forms.HiddenInput)
    default = forms.BooleanField(initial=True, required=False)


class SearchForm(forms.Form):
    """A form for searching a single model."""

    q = forms.CharField(
        required=False, label="Search", widget=forms.TextInput(attrs={"type": "search"})
    )


class StripeForm(forms.Form):
    """A form to collect a stripe token for a given amount and email."""

    # remove after crowdunds and donations moved to stripe
    stripe_pk = forms.CharField(
        initial=settings.STRIPE_PUB_KEY, required=False, widget=forms.HiddenInput
    )
    stripe_token = forms.CharField(
        widget=forms.HiddenInput(attrs={"autocomplete": "off"})
    )
    stripe_email = forms.EmailField(widget=forms.HiddenInput)
    stripe_fee = forms.IntegerField(initial=0, required=False, widget=forms.HiddenInput)
    stripe_label = forms.CharField(
        initial="Buy", required=False, widget=forms.HiddenInput
    )
    stripe_description = forms.CharField(required=False, widget=forms.HiddenInput)
    stripe_bitcoin = forms.BooleanField(
        initial=True, required=False, widget=forms.HiddenInput
    )
    stripe_amount = forms.IntegerField(min_value=0)
    type = forms.ChoiceField(choices=(("one-time", "One Time"), ("monthly", "Monthly")))


class DonateForm(StripeForm):
    """A form for donations"""

    name = forms.CharField(required=False)
    phone = PhoneNumberField(required=False)
    why = forms.CharField(required=False)
    address = forms.CharField(required=False)
