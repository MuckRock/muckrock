# -*- coding: utf-8 -*-
"""Fields for the Crowdsource application"""

from django import forms


class Field(object):
    """Base field for crowdsource form"""
    accepts_choices = False


class TextField(Field):
    """A text field"""
    name = 'text'
    field = forms.CharField


class SelectField(Field):
    """A select field"""
    name = 'select'
    field = forms.ChoiceField
    accepts_choices = True


FIELDS = [
        TextField,
        SelectField,
        ]


FIELD_CHOICES = [(f.name, f.name) for f in FIELDS]


FIELD_DICT = {f.name: f for f in FIELDS}
