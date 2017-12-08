"""
Forms for data sets
"""

from django import forms
from django.core.exceptions import ValidationError

import os.path

class DataSetUploadForm(forms.Form):
    """Form for uploading a CSV to create a new data set"""
    name = forms.CharField(max_length=255)
    data_file = forms.FileField(help_text='CSV or Excel file')

    def clean_data_file(self):
        """Ensure data file is an appropriate type"""
        ext = os.path.splitext(self.cleaned_data['data_file'].name)[1]
        if ext not in ('.csv', '.xls', '.xlsx'):
            raise ValidationError('Data file must be a csv/xls/xlsx')
