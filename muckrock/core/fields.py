"""
Custom fields

EmailsListField - http://djangosnippets.org/snippets/1958/
GroupedModelChoiceField - http://djangosnippets.org/snippets/1968/
"""

# Django
from django import forms
from django.core.validators import EmailValidator, ValidationError, validate_email
from django.db.models import CharField, FileField
from django.forms.models import ModelChoiceField, ModelChoiceIterator
from django.utils.translation import gettext as _

# Standard Library
import os
import re
from email.utils import parseaddr

email_separator_re = re.compile(r"[^\w\.\-\+\&@_]+")


# https://code.djangoproject.com/ticket/11027
# edited - only filename is stored in db
def filefield_maxlength_validator(value):
    """"Check if absolute file path can fit in database table"""

    if not hasattr(value, "field"):
        # images sent in via API do not have a field
        return value

    filename = value.field.generate_filename(value.instance, value.name)
    bytes_filename = len(filename.encode("utf-8"))  # filename length in bytes

    # File path length should fit in table cell
    if bytes_filename > value.field.max_length:
        try:
            if os.path.isfile(value.path):
                os.remove(value.path)
        except NotImplementedError:
            # if we are using S3, there path is not implemented
            # it also doesn't appear to be saved to S3 yet,
            # so no need to delete
            pass
        raise forms.ValidationError(_("File name too long."))
    return value


FileField.default_validators = FileField.default_validators[:] + [
    filefield_maxlength_validator
]


class EmailsListField(CharField):
    """Multi email field"""

    # pylint: disable=too-many-public-methods

    widget = forms.Textarea

    def clean(self, value, model_instance):
        """Validates list of email addresses"""
        super(EmailsListField, self).clean(value, model_instance)

        emails = email_separator_re.split(value)

        if not emails:
            raise forms.ValidationError(_("Enter at least one e-mail address."))

        for email in emails:
            validate_email(email)

        return value


class FullEmailValidator(EmailValidator):
    """Validate email addresses with full names"""

    # http://djangosnippets.org/snippets/2635/

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


class EmptyLastModelChoiceIterator(ModelChoiceIterator):
    """Put the empty choice last"""

    def __iter__(self):
        # pylint: disable=stop-iteration-return
        iter_self = super(EmptyLastModelChoiceIterator, self).__iter__()
        empty = next(iter_self)
        for obj in iter_self:
            yield obj
        yield empty


class EmptyLastModelChoiceField(ModelChoiceField):
    """Model Choice Field that puts the empty choice last"""

    iterator = EmptyLastModelChoiceIterator
