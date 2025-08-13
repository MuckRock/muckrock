"""
Views for the news application
"""

# Django
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Prefetch, Q
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView
from django.views.generic.dates import (
    DateDetailView,
    DayArchiveView,
    MonthArchiveView,
    YearArchiveView,
)

from fuzzywuzzy import fuzz, process

# MuckRock
from muckrock.core.utils import cache_get_or_set
from muckrock.core.views import (
    MRAutocompleteView,
    MRSearchFilterListView,
    PaginationMixin
)
from muckrock.news.filters import ArticleDateRangeFilterSet
from muckrock.news.models import Article
from muckrock.project.forms import ProjectManagerForm
from muckrock.project.models import Project
from muckrock.tags.models import Tag, normalize


class NewsDetail(DateDetailView):
    """View for news detail"""

    date_field = "pub_date"

    def get_template_names(self):
        """Use a different template for scrollama articles"""
        if self.object.scrollama:
            return ["news/detail_scrollama.html"]
        else:
            return ["news/detail.html"]

    def get_queryset(self):
        """Get articles for this view"""
        queryset = (
            Article.objects.prefetch_authors()
            .prefetch_editors()
            .prefetch_related("tags", "projects")
        )
        if self.request.user.is_staff:
            return queryset.all()
        else:
            return queryset.get_published()

    def get_allow_future(self):
        """Can future posts be seen?"""
        return self.request.user.is_staff

    def get_related_articles(self, article):
        """Get articles related to the current one."""
        projects = list(article.projects.all())
        tags = list(article.tags.all())
        # articles in the same project as this one
        project_filter = Q(projects__in=projects)
        # articles with the same tag as this one
        tag_filter = Q(tags__in=tags)
        # articles in projects with the same tag as this one
        project_tag_filter = Q(projects__tags__in=tags)
        published = (
            Article.objects.get_published()
            .only("image", "title", "slug", "pub_date")
            .exclude(pk=article.pk)
            .order_by()
            .prefetch_authors()
        )
        related_articles = (
            published.filter(project_filter)
            .union(published.filter(tag_filter), published.filter(project_tag_filter))
            .order_by("-pub_date")
        )
        return related_articles[:4]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["projects"] = context["object"].projects.all()
        context["foias"] = (
            context["object"]
            .foias.get_public()
            .select_related_view()
            .get_public_file_count()
        )
        context["related_articles"] = self.get_related_articles(context["object"])
        context["sidebar_admin_url"] = reverse(
            "admin:news_article_change", args=(context["object"].pk,)
        )
        context["stripe_pk"] = settings.STRIPE_PUB_KEY
        # if the user is staff, do not cache the page, so they can
        # use the project and tag forms
        if self.request.user.is_staff:
            context["news_cache_timeout"] = 0
        else:
            context["news_cache_timeout"] = settings.DEFAULT_CACHE_TIMEOUT
        context["authors"] = (
            context["object"]
            .authors.select_related("profile")
            .order_by("authorship__order")
        )
        context["editors"] = context["object"].editors.select_related("profile")
        return context

    def post(self, request, **kwargs):
        """Handles POST requests on article pages"""
        article = self.get_object()
        authorized = self.request.user.is_staff
        action = request.POST.get("action")
        clear_cache = False
        if not authorized:
            return HttpResponseForbidden()
        if action == "projects":
            form = ProjectManagerForm(request.POST, user=request.user)
            if form.is_valid():
                projects = form.cleaned_data["projects"]
                article.projects.set(projects)
                clear_cache = True
        tags = request.POST.getlist("tags")
        if tags:
            tag_set = set()
            for tag in tags:
                new_tag, _ = Tag.objects.get_or_create(name=normalize(tag))
                tag_set.add(new_tag)
            article.tags.set(tag_set)
            clear_cache = True
        if clear_cache:
            article.clear_cache()
        return redirect(article)


class NewsExploreView(TemplateView):
    """Shows the most interesting and worthwhile articles."""

    template_name = "news/explore.html"

    def get_context_data(self, **kwargs):
        """Adds interesting articles to the explore page."""
        context = super().get_context_data(**kwargs)
        recent_articles = cache_get_or_set(
            "hp:articles",
            lambda: (
                Article.objects.get_published().prefetch_related(
                    "authors", "authors__profile", "projects"
                )[:5]
            ),
            600,
        )
        context["featured_projects"] = (
            Project.objects.get_viewable(self.request.user)
            .filter(featured=True)
            .prefetch_related(
                Prefetch(
                    "articles__authors", queryset=User.objects.select_related("profile")
                )
            )
            .optimize()
        )
        context["recent_articles"] = recent_articles
        context["top_tags"] = Article.tags.most_common()[:15]
        return context


class NewsYear(PaginationMixin, YearArchiveView):
    """View for year archive"""

    date_field = "pub_date"
    make_object_list = True
    queryset = Article.objects.get_published().prefetch_authors()
    template_name = "news/archives/year_archive.html"


class NewsMonth(PaginationMixin, MonthArchiveView):
    """View for month archive"""

    date_field = "pub_date"
    make_object_list = True
    queryset = Article.objects.get_published().prefetch_authors()
    template_name = "news/archives/month_archive.html"


class NewsDay(PaginationMixin, DayArchiveView):
    """View for day archive"""

    date_field = "pub_date"
    make_object_list = True
    queryset = Article.objects.get_published().prefetch_authors()
    template_name = "news/archives/day_archive.html"


class NewsListView(MRSearchFilterListView):
    """List of news articles"""

    model = Article
    title = "News"
    filter_class = ArticleDateRangeFilterSet
    template_name = "news/list.html"
    default_sort = "pub_date"
    default_order = "desc"
    queryset = Article.objects.get_published().prefetch_authors()
    paginate_by = 10
    sort_map = {}

    def get_context_data(self, **kwargs):
        """Add a list of all the years we've published to the context."""
        context = super().get_context_data(**kwargs)
        articles_by_date = self.queryset.order_by("pub_date")
        if not articles_by_date.exists():
            raise Http404
        years = list(
            range(
                articles_by_date.first().pub_date.year,
                articles_by_date.last().pub_date.year + 1,
            )
        )
        years.reverse()
        context["years"] = years
        return context


class ArticleAutocomplete(MRAutocompleteView):
    """Autocomplete for picking articles"""

    queryset = (
        Article.objects.get_published()
        .prefetch_related(Prefetch("authors", User.objects.select_related("profile")))
        .distinct()
    )
    search_fields = ["title", "tags__name"]
    template = "autocomplete/article.html"

    def get_queryset(self):
        """Filter by project"""

        queryset = super().get_queryset()

        queryset, project = self._filter_by_project(queryset)

        exclude = self.forwarded.get("self", [])
        queryset = queryset.exclude(pk__in=exclude).order_by("-pub_date")[:10]

        if project:
            fuzzy_choices = self._fuzzy_choices(self.q, project, exclude)
            return self.queryset.filter(
                pk__in=[a.pk for a in queryset] + [a[2].pk for a in fuzzy_choices]
            ).order_by("-pub_date")
        else:
            return queryset

    def _filter_by_project(self, queryset):
        """If a project is forwarded, filter by it"""
        if "project" not in self.forwarded:
            return queryset, None

        try:
            project_id = self.forwarded["project"]
        except (TypeError, IndexError):
            # if project is not a single element list, something went wrong
            # do not filter
            return queryset, None

        try:
            project = Project.objects.get(pk=project_id)
            return project
        except Project.DoesNotExist:
            return queryset, None

    def _fuzzy_choices(self, query, project, exclude):
        """Do fuzzy matching for additional choices"""
        choices = self.queryset.filter(project=project).exclude(pk__in=exclude)
        return process.extractBests(
            query,
            {a: a.name for a in choices},
            scorer=fuzz.partial_ratio,
            score_cutoff=83,
            limit=10,
        )
