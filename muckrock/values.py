"""
Custom Values for dbsettings
"""

from django import forms

import dbsettings

# pylint: disable=invalid-name

class TextValue(dbsettings.values.Value):
    """Text area db value"""
    class field(forms.CharField):
        """Field for text value"""
        def __init__(self, *args, **kwargs):
            forms.CharField.__init__(self, *args, **kwargs)
            self.required = False
        widget = forms.Textarea
