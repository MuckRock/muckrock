"""Site wide modl utilities"""

from django.db.models import Func, IntegerField, DateTimeField

# pylint: disable=abstract-method

class ExtractDay(Func):
    """DB function to extract the day from a time interval"""
    template = 'EXTRACT(DAY FROM %(expressions)s)'

    def __init__(self, expression, output_field=None, **extra):
        if output_field is None:
            output_field = IntegerField()
        super(ExtractDay, self).__init__(
                expression, output_field=output_field, **extra)

# This is built in in Django 1.9
class Now(Func):
    """DB Function to get the current time"""
    template = 'CURRENT_TIMESTAMP'

    def __init__(self, output_field=None, **extra):
        if output_field is None:
            output_field = DateTimeField()
        super(Now, self).__init__(output_field=output_field, **extra)

    def as_postgresql(self, compiler, connection):
        """
        Postgres' CURRENT_TIMESTAMP means "the time at the start of the
        transaction". We use STATEMENT_TIMESTAMP to be cross-compatible with
        other databases.
        """
        self.template = 'STATEMENT_TIMESTAMP()'
        return self.as_sql(compiler, connection)
