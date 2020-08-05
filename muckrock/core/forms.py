"""
Forms for MuckRock
"""

# Django
from django import forms
from django.conf import settings

# Third Party
from dal.autocomplete import TaggitSelect2
from taggit.forms import TagField


class TagManagerForm(forms.Form):
    """A form with an autocomplete input for tags"""

    tags = TagField(
        widget=TaggitSelect2(url="tag-autocomplete", attrs={"data-placeholder": "Tags"})
    )

    def __init__(self, *args, **kwargs):
        required = kwargs.pop("required", True)
        super(TagManagerForm, self).__init__(*args, **kwargs)
        self.fields["tags"].required = required


class NewsletterSignupForm(forms.Form):
    """A form for adding an email to a MailChimp mailing list."""

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"placeholder": "email address"})
    )
    list = forms.CharField(widget=forms.HiddenInput)
    default = forms.BooleanField(initial=True, required=False)


class SearchForm(forms.Form):
    """A form for searching a single model."""

    # pylint: disable=invalid-name
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
