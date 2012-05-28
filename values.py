"""
Custom Values for dbsettings
"""

from django import forms

import dbsettings

class TextValue(dbsettings.values.Value):
    """Text area db value"""
    # pylint: disable=C0103
    class field(forms.CharField):
        """Field for text value"""
        def __init__(self, *args, **kwargs):
            forms.CharField.__init__(self, *args, **kwargs)
            self.required = False
        widget = forms.Textarea
