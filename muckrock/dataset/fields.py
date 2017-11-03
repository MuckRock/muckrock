"""
Field types for data sets
"""

from django.core.exceptions import ValidationError
from django.core.validators import (
        RegexValidator,
        EmailValidator,
        URLValidator,
        )

import calendar
import re


class Field(object):
    """A dataset field"""
    @classmethod
    def validate(cls, value):
        """Is this value valid for this type?"""
        try:
            cls.validator(value)
        except ValidationError:
            return False
        else:
            return True


class TextField(Field):
    """A text field"""
    name = 'Text'
    slug = 'text'
    formatter = 'plaintext'
    editor = '"input"'
    sort_type = 'text'

    @classmethod
    def validate(cls, value):
        """Is this value valid for this type?"""
        return True


class MultiTextField(Field):
    """A text field"""
    name = 'Multiline Text'
    slug = 'multi'
    formatter = 'textarea'
    editor = '"textarea"'
    sort_type = 'text'

    @classmethod
    def validate(cls, value):
        """Is this value valid for this type?"""
        return '\n' in value


class NumberField(Field):
    """A number field"""
    name = 'Number'
    slug = 'number'
    formatter = 'plaintext'
    editor = '"number"'
    sort_type = 'decimal'
    validator = RegexValidator(regex=r'^-?[0-9]+(?:[.][0-9]+)?$')


class MoneyField(Field):
    """A money field"""
    name = 'Money'
    slug = 'money'
    formatter = 'money'
    editor = '"number"'
    sort_type = 'decimal'
    validator = RegexValidator(regex=r'^-?[0-9]+(?:[.][0-9]+)?$')


class EmailField(Field):
    """An email field"""
    name = 'Email'
    slug = 'email'
    formatter = 'email'
    editor = '"input"'
    sort_type = 'text'
    validator = EmailValidator()


class URLField(Field):
    """An email field"""
    name = 'URL'
    slug = 'url'
    formatter = 'link'
    editor = '"input"'
    sort_type = 'text'
    validator = URLValidator()


class BoolField(Field):
    """A boolean field"""
    name = 'Boolean'
    slug = 'bool'
    formatter = 'tickCross'
    editor = 'selectEditor'
    sort_type = 'text'
    validator = RegexValidator(
            regex=r'^(?:true|1|false|0)$',
            flags=re.IGNORECASE,
            )


class ColorField(Field):
    """A color field"""
    name = 'Color'
    slug = 'color'
    formatter = 'color'
    editor = '"input"'
    sort_type = 'text'
    validator = RegexValidator(
            regex=r'^#[0-9a-f]{3}(?:[0-9a-f]{3})?$',
            flags=re.IGNORECASE,
            )


class ChoiceField(Field):
    """A choice field"""
    name = 'Choice'
    slug = 'choice'
    formatter = 'plaintext'
    editor = 'selectEditor'
    sort_type = 'text'
    max_choices = 7

    @classmethod
    def validate_all(cls, values):
        """Is there less than a certain number of choices among all values?"""
        return len(set(values)) < cls.max_choices

MONTH_NAME = '|'.join(calendar.month_name[1:])
MONTH_ABBR = '|'.join(calendar.month_abbr[1:])
MONTH_NUM = r'0?[1-9]|1[0-2]'
MONTH_RE = r'(?:{}|{}|{})'.format(MONTH_NAME, MONTH_ABBR, MONTH_NUM)
YEAR_RE = r'(?:\d{2}|\d{4})'
DAY_RE = r'(?:0?[1-9]|[12][0-9]|3[01])'


class DateField(Field):
    """A date field"""
    name = 'Date'
    slug = 'date'
    formatter = 'plaintext'
    editor = '"input"'
    sort_type = 'date'
    validator = RegexValidator(
            regex=r'^(?:{y}-{m}-{d}|{m} {d}, {y}|{m}/{d}/{y}|{m}-{d}-{y})'
                .format(
                    m=MONTH_RE,
                    d=DAY_RE,
                    y=YEAR_RE,
                    ),
            flags=re.IGNORECASE,
            )

FIELDS = [
        MultiTextField,
        NumberField,
        MoneyField,
        EmailField,
        URLField,
        BoolField,
        ColorField,
        DateField,
        ChoiceField,
        TextField,
        ]
FIELD_DICT = {f.slug: f for f in FIELDS}
