"""Site wide model utilities"""

# pylint: disable=abstract-method

# Django
from django.core.cache import cache
from django.db.models import (
    CASCADE,
    CharField,
    ForeignKey,
    Func,
    IntegerField,
    JSONField,
    ManyToManyField,
    Model,
    TextField,
)


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


class HomePage(SingletonModel):
    about_heading = CharField(
        max_length=255,
        default="We give you the tools to keep government transparent and accountable",
    )
    about_paragraph = TextField(
        blank=True,
        default=(
            "MuckRock Foundation is a nonprofit, collaborative organization and "
            "newsroom that brings together journalists, researchers and the "
            "public to request, analyze and share government information, "
            "making politics more transparent and democracy more informed."
        ),
    )
    product_stats = JSONField(
        blank=True,
        default=dict,
        help_text="JSON object for DocumentCloud and Data Liberation Project stats",
    )

    expertise_sections = JSONField(
        blank=True,
        default=list,
        help_text=(
            "JSON array of expertise sections, each with title, subtitle, "
            "description, and links (title, href, text, icon)",
        ),
    )

    class Meta:
        verbose_name = "Home Page"
        verbose_name_plural = "Home Page"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Invalidate homepage caches on save
        cache.delete("homepage_obj")
        cache.delete("homepage_featured_project_slots")

    def __str__(self):
        return "Home Page"


class FeaturedProjectSlot(Model):
    homepage = ForeignKey(
        HomePage, on_delete=CASCADE, related_name="featured_project_slots"
    )
    order = IntegerField(default=0, help_text="Order of appearance on homepage")
    project = ForeignKey(
        "project.Project", on_delete=CASCADE, related_name="homepage_slots"
    )
    articles = ManyToManyField(
        "news.Article", blank=True, related_name="featured_in_slots"
    )

    class Meta:
        ordering = ["order"]
        verbose_name = "Featured Project Slot"
        verbose_name_plural = "Featured Project Slots"

    def __str__(self):
        return f"{self.project} (Order: {self.order})"
