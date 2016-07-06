"""
Custom fields

EmailsListField - http://djangosnippets.org/snippets/1958/
GroupedModelChoiceField - http://djangosnippets.org/snippets/1968/
"""

import os
import re
from email.utils import parseaddr
from itertools import groupby

from django import forms
from django.core.validators import EmailValidator, ValidationError, validate_email
from django.db.models import CharField, FileField
from django.forms.models import ModelChoiceIterator, ModelChoiceField
from django.utils.translation import ugettext as _

from phonenumbers import (
        NumberParseException,
        PhoneNumberFormat,
        format_number,
        parse,
        )

email_separator_re = re.compile(r'[^\w\.\-\+\&@_]+')

# https://code.djangoproject.com/ticket/11027
# edited - only filename is stored in db
def filefield_maxlength_validator(value):
    """"Check if absolute file path can fit in database table"""

    filename = value.field.generate_filename(value.instance, value.name)
    bytes_filename = len(filename.encode('utf-8')) # filename length in bytes

    # File path length should fit in table cell
    if bytes_filename > value.field.max_length:
        if os.path.isfile(value.path):
            os.remove(value.path)
        raise forms.ValidationError(_(u'File name too long.'))
    return value


FileField.default_validators = FileField.default_validators[:] + [filefield_maxlength_validator]


class EmailsListField(CharField):
    """Multi email field"""
    # pylint: disable=too-many-public-methods

    widget = forms.Textarea

    def clean(self, value, model_instance):
        """Validates list of email addresses"""
        super(EmailsListField, self).clean(value, model_instance)

        emails = email_separator_re.split(value)

        if not emails:
            raise forms.ValidationError(_(u'Enter at least one e-mail address.'))

        for email in emails:
            validate_email(email)

        return value


class FullEmailValidator(EmailValidator):
    """Validate email addresses with full names"""
    #http://djangosnippets.org/snippets/2635/
    # pylint: disable=too-few-public-methods

    def __call__(self, value):
        # pylint: disable=unused-variable
        try:
            super(FullEmailValidator, self).__call__(value)
        except ValidationError:
            # Trivial case failed. Try for possible Full Name <email@address>
            fullname, email = parseaddr(value)
            super(FullEmailValidator, self).__call__(email)


validate_full_email = FullEmailValidator()


class FullEmailField(forms.EmailField):
    """Email field that accepts full name format"""
    default_validators = [validate_full_email]

    def clean(self, value):
        """Accept full name emails - only store the email part"""
        # pylint: disable=unused-variable

        super(FullEmailField, self).clean(value)
        fullname, email = parseaddr(value)
        return email


class GroupedModelChoiceField(ModelChoiceField):
    """Form field for grouped model choice"""
    def __init__(self, group_by_field, group_label=None, *args, **kwargs):
        """
        group_by_field is the name of a field on the model
        group_label is a function to return a label for each choice group
        """
        super(GroupedModelChoiceField, self).__init__(*args, **kwargs)
        self.group_by_field = group_by_field
        if group_label is None:
            self.group_label = lambda group: group
        else:
            self.group_label = group_label

    def _get_choices(self):
        """
        Exactly as per ModelChoiceField except returns new iterator class
        """
        if hasattr(self, '_choices'):
            return self._choices
        return GroupedModelChoiceIterator(self)
    choices = property(_get_choices, ModelChoiceField._set_choices)


class GroupedModelChoiceIterator(ModelChoiceIterator):
    """Iterator for grouped model choice"""
    # pylint: disable=too-few-public-methods
    # pylint: disable=line-too-long
    def __iter__(self):
        if self.field.empty_label is not None:
            yield (u"", self.field.empty_label)
        if self.field.cache_choices:
            if self.field.choice_cache is None:
                self.field.choice_cache = [
                    (self.field.group_label(group), [self.choice(ch) for ch in choices])
                    for group, choices in groupby(
                        self.queryset.all(),
                        key=lambda row: getattr(row, self.field.group_by_field)
                    )
                ]
            for choice in self.field.choice_cache:
                yield choice
        else:
            for group, choices in groupby(self.queryset.all(), key=lambda row: getattr(row, self.field.group_by_field)):
                yield (self.field.group_label(group), [self.choice(ch) for ch in choices])


# https://github.com/fusionbox/django-fusionbox/blob/master/fusionbox/forms/fields.py
class USDCurrencyField(forms.DecimalField):
    """Form field for entering dollar amounts."""
    def clean(self, value):
        """Allows an optional leading dollar sign, which gets stripped."""
        return super(USDCurrencyField, self).clean(value.lstrip('$'))


class PhoneNumberField(forms.CharField):
    """Phone number field using google's phone number library"""

    def clean(self, value):
        """Parse and format using google's phone number library"""
        try:
            phone = parse(value, 'US')
            return format_number(phone, PhoneNumberFormat.NATIONAL)
        except NumberParseException:
            raise ValidationError(
                    '%(value)s is not a valid phone number',
                    params={'value': value})
