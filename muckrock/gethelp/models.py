"""Models for the gethelp app"""

# Django
from django.db import models


class Category(models.Model):
    """An admin-editable help category"""

    slug = models.SlugField(max_length=20, unique=True)
    label = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.label


class Problem(models.Model):
    """An admin-editable help problem with optional self-referential nesting"""

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="problems",
    )
    title = models.CharField(max_length=255)
    resolution = models.TextField(blank=True)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children",
    )
    flag_category = models.CharField(
        max_length=40,
        blank=True,
        help_text="Maps to an existing flag category for staff triage",
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["category__order", "order"]

    def __str__(self):
        return self.title
