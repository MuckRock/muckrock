"""Site wide model utilities"""

# pylint: disable=abstract-method

# Django
from django.db.models import Func, IntegerField


# This is in django but does not support intervals until django 2.0
class ExtractDay(Func):
    """DB function to extract the day from a time interval"""
    template = 'EXTRACT(DAY FROM %(expressions)s)'

    def __init__(self, expression, output_field=None, **extra):
        if output_field is None:
            output_field = IntegerField()
        super(ExtractDay, self).__init__(
            expression, output_field=output_field, **extra
        )
