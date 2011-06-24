"""
Custom fields

EmailsListField - http://djangosnippets.org/snippets/1958/
GroupedModelChoiceField - http://djangosnippets.org/snippets/1968/
"""

import re
from itertools import groupby

from django.core.validators import email_re
from django.db.models import CharField
from django.forms import Textarea, ValidationError
from django.forms.models import ModelChoiceIterator, ModelChoiceField
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
    # pylint: disable-msg=R0903
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
