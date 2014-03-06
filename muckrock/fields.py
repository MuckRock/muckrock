"""
Custom fields

EmailsListField - http://djangosnippets.org/snippets/1958/
GroupedModelChoiceField - http://djangosnippets.org/snippets/1968/
"""

import os
import re
from calendar import monthrange
from datetime import date
from email.utils import parseaddr
from itertools import groupby

from django import forms
from django.core.validators import email_re, EmailValidator, ValidationError
from django.db.models import CharField, FileField
from django.forms.models import ModelChoiceIterator, ModelChoiceField
from django.utils.translation import ugettext as _
from south.modelsinspector import add_introspection_rules

add_introspection_rules([], ["^muckrock\.fields\.EmailsListField"])

email_separator_re = re.compile(r'[^\w\.\-\+\&@_]+')

def _is_valid_email(email):
    """Validates an email address"""
    return email_re.match(email)


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
    # pylint: disable=R0904

    widget = forms.Textarea

    def clean(self, value, model_instance):
        """Validates list of email addresses"""
        super(EmailsListField, self).clean(value, model_instance)

        emails = email_separator_re.split(value)

        if not emails:
            raise forms.ValidationError(_(u'Enter at least one e-mail address.'))

        for email in emails:
            if not _is_valid_email(email):
                raise forms.ValidationError(_('%s is not a valid e-mail address.') % email)

        return value


class FullEmailValidator(EmailValidator):
    """Validate email addresses with full names"""
    #http://djangosnippets.org/snippets/2635/
    # pylint: disable=R0903

    def __call__(self, value):
        # pylint: disable=W0612
        try:
            super(FullEmailValidator, self).__call__(value)
        except ValidationError:
            # Trivial case failed. Try for possible Full Name <email@address>
            fullname, email = parseaddr(value)
            super(FullEmailValidator, self).__call__(email)

validate_full_email = FullEmailValidator(email_re, 'Enter a valid e-mail address.', 'invalid')


class FullEmailField(forms.EmailField):
    """Email field that accepts full name format"""
    default_validators = [validate_full_email]

    def clean(self, value):
        """Accept full name emails - only store the email part"""
        # pylint: disable=W0612

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
    # pylint: disable=R0903
    def __iter__(self):
        if self.field.empty_label is not None:
            yield (u"", self.field.empty_label)
        if self.field.cache_choices:
            if self.field.choice_cache is None:
                self.field.choice_cache = [
                    (self.field.group_label(group), [self.choice(ch) for ch in choices])
                        for group,choices in groupby(self.queryset.all(),
                            key=lambda row: getattr(row, self.field.group_by_field))
                ]
            for choice in self.field.choice_cache:
                yield choice
        else:
            for group, choices in groupby(self.queryset.all(),
                    key=lambda row: getattr(row, self.field.group_by_field)):
                yield (self.field.group_label(group), [self.choice(ch) for ch in choices])


 # CC widget and field: http://djangosnippets.org/snippets/907/
class CCExpWidget(forms.MultiWidget):
    """ Widget containing two select boxes for selecting the month and year"""

    def decompress(self, value):
        """Get month and year from date"""
        return [value.month, value.year] if value else [None, None]

    def format_output(self, rendered_widgets):
        """Join child widgets"""
        html = u' / '.join(rendered_widgets)
        return u'<span style="white-space: nowrap">%s</span>' % html


class CCExpField(forms.MultiValueField):
    """CC expiration date field"""
    EXP_MONTH = [(x, x) for x in xrange(1, 13)]
    EXP_YEAR = [(x, x) for x in xrange(date.today().year,
                                       date.today().year + 15)]
    default_error_messages = {
        'invalid_month': u'Enter a valid month.',
        'invalid_year': u'Enter a valid year.',
    }

    def __init__(self, *args, **kwargs):
        errors = self.default_error_messages.copy()
        if 'error_messages' in kwargs:
            errors.update(kwargs['error_messages'])
        fields = (
            forms.ChoiceField(choices=self.EXP_MONTH,
                error_messages={'invalid': errors['invalid_month']},
                widget=forms.Select(
                    attrs={'class': 'card-expiry-month stripe-sensitive required'})),
            forms.ChoiceField(choices=self.EXP_YEAR,
                error_messages={'invalid': errors['invalid_year']},
                widget=forms.Select(
                    attrs={'class': 'card-expiry-year stripe-sensitive required'})),
        )
        super(CCExpField, self).__init__(fields, *args, **kwargs)
        self.widget = CCExpWidget(widgets =
            [fields[0].widget, fields[1].widget])

    def clean(self, value):
        """Make sure the expiration date i sin the future"""
        exp = super(CCExpField, self).clean(value)
        if exp and date.today() > exp:
            raise forms.ValidationError(
            "The expiration date you entered is in the past.")
        return exp

    def compress(self, data_list):
        """Create a date from the month and year"""
        if data_list:
            if data_list[1] in forms.fields.EMPTY_VALUES:
                error = self.error_messages['invalid_year']
                raise forms.ValidationError(error)
            if data_list[0] in forms.fields.EMPTY_VALUES:
                error = self.error_messages['invalid_month']
                raise forms.ValidationError(error)
            year = int(data_list[1])
            month = int(data_list[0])
            # find last day of the month
            day = monthrange(year, month)[1]
            return date(year, month, day)
        return None


#https://github.com/fusionbox/django-fusionbox/blob/master/fusionbox/forms/fields.py
class USDCurrencyField(forms.DecimalField):
    """
    Form field for entering dollar amounts. Allows an optional leading dollar
    sign, which gets stripped.
    """
    def clean(self, value):
        return super(USDCurrencyField, self).clean(value.lstrip('$'))
