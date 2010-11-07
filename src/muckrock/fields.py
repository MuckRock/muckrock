"""
Custom fields
"""

import re

from django.core.validators import email_re
from django.db.models import CharField
from django.forms import Textarea, ValidationError
from django.utils.translation import ugettext as _
from south.modelsinspector import add_introspection_rules

add_introspection_rules([], ["^fields\.EmailsListField"])

email_separator_re = re.compile(r'[^\w\.\-\+@_]+')

def _is_valid_email(email):
    """Validates an email address"""
    return email_re.match(email)

class EmailsListField(CharField):
    """Multi email field"""
    # pylint: disable-msg=R0904

    widget = Textarea

    def clean(self, value, model_instance):
        """Validates list of email addresses"""
        super(EmailsListField, self).clean(value, model_instance)

        emails = email_separator_re.split(value)

        if not emails:
            raise ValidationError(_(u'Enter at least one e-mail address.'))

        for email in emails:
            if not _is_valid_email(email):
                raise ValidationError(_('%s is not a valid e-mail address.') % email)

        return value
