"""
Custom Values for dbsettings
"""

# Django
from django import forms

# Third Party
import dbsettings


class TextValue(dbsettings.values.Value):
    """Text area db value"""

    # pylint: disable=invalid-name
    class field(forms.CharField):
        """Field for text value"""

        def __init__(self, *args, **kwargs):
            forms.CharField.__init__(self, *args, **kwargs)
            self.required = False

        widget = forms.Textarea
