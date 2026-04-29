"""Models for the gethelp app"""

from django.db import models


class Problem(models.Model):
    """An admin-editable help problem with optional self-referential nesting"""

    CATEGORY_CHOICES = [
        ("managing", "Managing this request"),
        ("communications", "Communications and messages"),
        ("payments", "Checks and request payments"),
        ("documents", "Documents and files"),
        ("portals", "Agency portals and web forms"),
        ("appeals", "Appeals and public records advice"),
        ("proxy", "In-state proxy and proof of citizenship"),
    ]

    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
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
        ordering = ["category", "order"]

    def __str__(self):
        return self.title
