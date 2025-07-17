"""Site wide model utilities"""

# pylint: disable=abstract-method

# Django
from django.db.models import Func, IntegerField, Model


# This is in django but does not support intervals until django 2.0
class ExtractDay(Func):
    """DB function to extract the day from a time interval"""

    template = "EXTRACT(DAY FROM %(expressions)s)"

    def __init__(self, expression, output_field=None, **extra):
        if output_field is None:
            output_field = IntegerField()
        super().__init__(expression, output_field=output_field, **extra)


class NullIf(Func):
    """DB Function NULLIF"""

    function = "NULLIF"


class SingletonModel(Model):
    """
    Abstract base class for singleton models.
    """
    singleton_instance_id = 1

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = self.singleton_instance_id
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=cls.singleton_instance_id)
        return obj

    @classmethod
    def get_field_value(cls, field_name, default_value=None):
        obj = cls.load()
        return getattr(obj, field_name, default_value)