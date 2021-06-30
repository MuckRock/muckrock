"""
Filters for the news application
"""

# Django
from django.contrib.auth.models import User
from django.db.models import Count

# Third Party
import django_filters
from dal import forward

# MuckRock
from muckrock.core import autocomplete
from muckrock.core.filters import RangeWidget
from muckrock.news.models import Article
from muckrock.project.models import Project
from muckrock.tags.models import Tag


class ArticleDateRangeFilterSet(django_filters.FilterSet):
    """Allows a list of news items to be filtered by a date range, an author, or many
    tags."""

    projects = django_filters.ModelMultipleChoiceFilter(
        field_name="projects",
        queryset=lambda request: Project.objects.get_viewable(request.user),
        widget=autocomplete.ModelSelect2Multiple(
            url="project-autocomplete", attrs={"data-placeholder": "Search projects"}
        ),
    )
    authors = django_filters.ModelMultipleChoiceFilter(
        queryset=(
            User.objects.annotate(article_count=Count("authored_articles")).filter(
                article_count__gt=0
            )
        ),
        widget=autocomplete.ModelSelect2Multiple(
            url="user-autocomplete",
            attrs={"data-placeholder": "Search authors"},
            forward=(forward.Const(True, "authors"),),
        ),
    )
    pub_date = django_filters.DateFromToRangeFilter(
        label="Date Range",
        lookup_expr="contains",
        widget=RangeWidget(attrs={"class": "datepicker", "placeholder": "MM/DD/YYYY"}),
    )
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name="tags__name",
        queryset=Tag.objects.all(),
        label="Tags",
        widget=autocomplete.ModelSelect2Multiple(
            url="tag-autocomplete", attrs={"data-placeholder": "Search tags"}
        ),
    )

    class Meta:
        model = Article
        fields = ["projects", "authors", "pub_date"]
