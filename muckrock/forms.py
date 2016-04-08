"""
Forms for MuckRock
"""

from django import forms
from django.contrib.auth import forms as auth_forms
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.template import loader

from autocomplete_light import shortcuts as autocomplete_light
from autocomplete_light.contrib.taggit_field import TaggitField
from autocomplete_light.widgets import TextWidget
import six
from taggit.utils import edit_string_for_tags

from muckrock.agency.models import Agency
from muckrock.jurisdiction.models import Jurisdiction


class TaggitWidget(TextWidget):
    """built in one breaks on select_related... not sure why"""
    def render(self, name, value, attrs=None):
        if value is not None and not isinstance(value, six.string_types):
            value = edit_string_for_tags(
                [o.tag for o in value])
        return super(TaggitWidget, self).render(name, value, attrs)


class MRFilterForm(forms.Form):
    """A generic class to filter a list of items"""
    user = forms.ModelChoiceField(
        required=False,
        queryset=User.objects.all(),
        widget=autocomplete_light.ChoiceWidget(
            'UserAutocomplete',
            attrs={'placeholder': 'All Users'}))
    agency = forms.ModelChoiceField(
        required=False,
        queryset=Agency.objects.all(),
        widget=autocomplete_light.ChoiceWidget(
            'AgencyAutocomplete',
            attrs={'placeholder': 'All Agencies'}))
    jurisdiction = forms.ModelChoiceField(
        required=False,
        queryset=Jurisdiction.objects.all(),
        widget=autocomplete_light.ChoiceWidget(
            'JurisdictionAutocomplete',
            attrs={'placeholder': 'All Jurisdictions'}))
    tags = TaggitField(widget=TaggitWidget(
        'TagAutocomplete',
        attrs={
            'placeholder': 'All Tags (comma separated)',
            'data-autocomplete-minimum-characters': 1}))


class TagManagerForm(forms.Form):
    """A form with an autocomplete input for tags"""
    tags = TaggitField(widget=TaggitWidget(
        'TagAutocomplete',
        attrs={
            'placeholder': 'Tags',
            'data-autocomplete-minimum-characters': 1}))


class NewsletterSignupForm(forms.Form):
    """A form for adding an email to a MailChimp mailing list."""
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'email address'}))
    list = forms.CharField(widget=forms.HiddenInput)


class PasswordResetForm(auth_forms.PasswordResetForm):
    """Password reset form - subclass to bcc emails to diagnostics"""
    # pylint: disable=too-many-arguments

    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email, html_email_template_name=None):
        """
        Sends a django.core.mail.EmailMultiAlternatives to `to_email`.
        """
        subject = loader.render_to_string(subject_template_name, context)
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        body = loader.render_to_string(email_template_name, context)

        email_message = EmailMultiAlternatives(
                subject=subject,
                body=body,
                from_email=from_email,
                to=[to_email],
                bcc=['diagnostics@muckrock.com'],
                )
        if html_email_template_name is not None:
            html_email = loader.render_to_string(html_email_template_name, context)
            email_message.attach_alternative(html_email, 'text/html')

        email_message.send()
