"""Models for the gethelp app"""

# Django
from django.db import models
from django.utils.safestring import mark_safe

MARKDOWN_HELP_TEXT = mark_safe(
    "Supports Markdown — see the "
    '<a href="https://daringfireball.net/projects/markdown/syntax" '
    'target="_blank" rel="noopener">syntax guide</a>.'
)


class Category(models.Model):
    """An admin-editable help category"""

    slug = models.SlugField(max_length=20, unique=True)
    label = models.CharField(max_length=100)
    description = models.TextField(
        blank=True,
        help_text=mark_safe(
            "Optional intro shown above the list of problems in this category. "
            + MARKDOWN_HELP_TEXT
        ),
    )
    placeholder = models.CharField(
        max_length=255,
        blank=True,
        help_text=(
            "Placeholder text for the free-form contact textarea when this "
            "category is selected. Leave blank to use the site default."
        ),
    )
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
    resolution = models.TextField(
        blank=True,
        help_text=mark_safe(
            "How the user can resolve this problem on their own. " + MARKDOWN_HELP_TEXT
        ),
    )
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
    placeholder = models.CharField(
        max_length=255,
        blank=True,
        help_text=(
            "Placeholder text for the free-form contact textarea when this "
            "problem is selected. Overrides the category placeholder. Leave "
            "blank to fall back to the category or site default."
        ),
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["category__order", "order"]

    def __str__(self):
        return self.title
