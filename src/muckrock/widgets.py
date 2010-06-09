"""
Custom widgets used throughout the website
"""

from django import forms

class CalendarWidget(forms.TextInput):
    """Text widget with a jQuery UI datepicker"""

    class Media:
        # pylint: disable-msg=R0903
        css = {'all': ('/static/css/jquery-ui-1.8.1.custom.css',) }
        js = (
                'http://ajax.googleapis.com/ajax/libs/jquery/1.4.2/jquery.min.js',
                'http://ajax.googleapis.com/ajax/libs/jqueryui/1.8.2/jquery-ui.min.js',
                '/static/js/datepicker.js',
             )
