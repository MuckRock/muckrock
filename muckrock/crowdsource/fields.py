# -*- coding: utf-8 -*-
"""Fields for the Crowdsource application"""

# Django
from django import forms


class Field(object):
    """Base field for crowdsource form"""
    accepts_choices = False
    widget = None
    multiple_values = False

    def get_form_field(self, field, **kwargs):
        """Create the form field"""
        kwargs['label'] = field.label
        kwargs['required'] = field.required
        if self.accepts_choices:
            kwargs['choices'] = [(c.value, c.choice)
                                 for c in field.choices.all()]
        if self.widget:
            kwargs['widget'] = self.widget
        if field.help_text:
            kwargs['help_text'] = field.help_text
        return self.field(**kwargs)


class TextField(Field):
    """A text field"""
    name = 'text'
    field = forms.CharField


class SelectField(Field):
    """A select field"""
    name = 'select'
    field = forms.ChoiceField
    accepts_choices = True


class CheckboxField(Field):
    """A checkbox field"""
    # this is checkbox2 due to name clash in the jquery formbuilder code
    name = 'checkbox2'
    field = forms.BooleanField

    def get_form_field(self, field, **kwargs):
        """Checkboxes should never be required"""
        form_field = super(CheckboxField, self).get_form_field(field)
        form_field.required = False
        return form_field


class CheckboxGroupField(Field):
    """A checkbox group field"""
    name = 'checkbox-group'
    field = forms.MultipleChoiceField
    accepts_choices = True
    widget = forms.CheckboxSelectMultiple
    multiple_values = True


class DateField(Field):
    """A date field"""
    name = 'date'
    field = forms.DateField

    def get_form_field(self, field, **kwargs):
        """Set a class for date fields"""
        form_field = super(DateField, self).get_form_field(field)
        form_field.widget.attrs['class'] = 'datepicker-simple'
        return form_field


class NumberField(Field):
    """A number field"""
    name = 'number'
    field = forms.FloatField

    def get_form_field(self, field, **kwargs):
        """Set min and max attributes for numbers"""
        if field.min is not None:
            kwargs['min_value'] = field.min
        if field.max is not None:
            kwargs['max_value'] = field.max
        return super(NumberField, self).get_form_field(field, **kwargs)


class TextareaField(Field):
    """A text area field"""
    name = 'textarea'
    field = forms.CharField

    def get_form_field(self, field, **kwargs):
        """Set a max length for text areas"""
        kwargs['widget'] = forms.Textarea
        kwargs['max_length'] = 2000
        return super(TextareaField, self).get_form_field(field, **kwargs)


FIELDS = [
    TextField,
    SelectField,
    CheckboxField,
    CheckboxGroupField,
    DateField,
    NumberField,
    TextareaField,
]

FIELD_CHOICES = [(f.name, f.name) for f in FIELDS]

FIELD_DICT = {f.name: f for f in FIELDS}
