"""Validation routines for forms"""


def validate_date_order(begin_field, end_field):
    """Creates a clean method to be added to forms to validate one date comes before another"""

    def clean(self):
        """Validate end date comes after begin date"""
        date_begin = self.cleaned_data.get(begin_field)
        date_end = self.cleaned_data.get(end_field)

        if date_begin and date_end and date_begin >= date_end:
            # pylint: disable=protected-access
            self._errors[end_field] = self.error_class([
                '%s must be later than %s' % (end_field, begin_field)
            ])

        return self.cleaned_data

    return clean
