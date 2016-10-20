"""
Views for the news application
"""

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models import Prefetch, Q
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, get_object_or_404
from django.views.generic.list import ListView
from django.views.generic.dates import (
    YearArchiveView,
    MonthArchiveView,
    DayArchiveView,
    DateDetailView
)

from rest_framework import viewsets
from rest_framework.permissions import DjangoModelPermissions
import django_filters

from muckrock.news.filters import (
    ArticleFilterSet,
    ArticleDateRangeFilterSet,
    ArticleAuthorFilterSet
)
from muckrock.news.models import Article
from muckrock.news.serializers import ArticleSerializer
from muckrock.project.forms import ProjectManagerForm
from muckrock.tags.models import Tag, parse_tags
from muckrock.views import MRFilterableListView, PaginationMixin, FilterMixin

# pylint: disable=too-many-ancestors

class NewsDetail(DateDetailView):
    """View for news detail"""
    template_name = 'news/detail.html'
    date_field = 'pub_date'

    def get_queryset(self):
        """Get articles for this view"""
        queryset = Article.objects.prefetch_related(
                Prefetch('authors',
                    queryset=User.objects.select_related('profile')),
                Prefetch('editors',
                    queryset=User.objects.select_related('profile')))
        if self.request.user.is_staff:
            return queryset.all()
        else:
            return queryset.get_published()

    def get_allow_future(self):
        """Can future posts be seen?"""
        return self.request.user.is_staff

    def get_related_articles(self):
        """Get articles related to the current one."""
        article = self.get_object()
        # articles in the same project as this one
        project_filter = Q(projects__in=article.projects.all())
        # articles with the same tag as this one
        tag_filter = Q(tags__in=article.tags.all())
        # articles in projects with the same tag as this one
        project_tag_filter = Q(projects__tags__in=article.tags.all())
        related_articles = Article.objects.get_published().filter(
            project_filter|tag_filter|project_tag_filter
        ).distinct().exclude(pk=article.pk)
        return related_articles[:4]

    def get_context_data(self, **kwargs):
        context = super(NewsDetail, self).get_context_data(**kwargs)
        context['projects'] = context['object'].projects.all()
        context['foias'] = (context['object'].foias
                .select_related_view().get_public_file_count())
        context['related_articles'] = self.get_related_articles()
        context['sidebar_admin_url'] = reverse('admin:news_article_change',
            args=(context['object'].pk,))
        context['stripe_pk'] = settings.STRIPE_PUB_KEY
        return context

    def post(self, request, **kwargs):
        """Handles POST requests on article pages"""
        # pylint:disable=unused-argument
        article = self.get_object()
        authorized = self.request.user.is_staff
        action = request.POST.get('action')
        if not authorized:
            return HttpResponseForbidden()
        if action == 'projects':
            form = ProjectManagerForm(request.POST)
            if form.is_valid():
                projects = form.cleaned_data['projects']
                article.projects = projects
        tags = request.POST.get('tags')
        if tags:
            tag_set = set()
            for tag in parse_tags(tags):
                new_tag, _ = Tag.objects.get_or_create(name=tag)
                tag_set.add(new_tag)
            article.tags.set(*tag_set)
        return redirect(article)


class NewsYear(PaginationMixin, YearArchiveView):
    """View for year archive"""
    allow_empty = True
    date_field = 'pub_date'
    make_object_list = True
    queryset = Article.objects.get_published().prefetch_related(
            Prefetch('authors', queryset=User.objects.select_related('profile')))
    template_name = 'news/archives/year_archive.html'


class NewsMonth(PaginationMixin, MonthArchiveView):
    """View for month archive"""
    allow_empty = True
    date_field = 'pub_date'
    make_object_list = True
    queryset = Article.objects.get_published().prefetch_related(
            Prefetch('authors', queryset=User.objects.select_related('profile')))
    template_name = 'news/archives/month_archive.html'


class NewsDay(PaginationMixin, DayArchiveView):
    """View for day archive"""
    allow_empty = True
    date_field = 'pub_date'
    make_object_list = True
    queryset = Article.objects.get_published().prefetch_related(
            Prefetch('authors', queryset=User.objects.select_related('profile')))
    template_name = 'news/archives/day_archive.html'


class NewsListView(MRFilterableListView):
    """List of news articles"""
    model = Article
    title = 'News'
    filter_class = ArticleDateRangeFilterSet
    template_name = 'news/list.html'
    default_sort = 'pub_date'
    default_order = 'desc'
    queryset = Article.objects.get_published().prefetch_related(
            Prefetch('authors', queryset=User.objects.select_related('profile')))

    def get_context_data(self, **kwargs):
        """Add a list of all the years we've published to the context."""
        context = super(NewsListView, self).get_context_data(**kwargs)
        articles_by_date = self.queryset.order_by('pub_date')
        years = range(
            articles_by_date.first().pub_date.year,
            articles_by_date.last().pub_date.year + 1, # the range function stops at n - 1
        )
        years.reverse()
        context['years'] = years
        return context


class AuthorArchiveView(NewsListView):
    """List of news articles by author"""
    filter_class = ArticleAuthorFilterSet
    template_name = 'news/author.html'

    def get_author(self):
        """Return the author this view is referencing."""
        return get_object_or_404(User, username=self.kwargs.get('username'))

    def get_queryset(self):
        """Returns just articles for the specific author."""
        return self.queryset.filter(authors=self.get_author())

    def get_context_data(self, **kwargs):
        context = super(AuthorArchiveView, self).get_context_data(**kwargs)
        context.update({
            'author': self.get_author()
        })
        return context

class ArticleViewSet(viewsets.ModelViewSet):
    """API views for Article"""
    # pylint: disable=too-many-ancestors
    # pylint: disable=too-many-public-methods
    model = Article
    serializer_class = ArticleSerializer
    permission_classes = (DjangoModelPermissions,)

    class Filter(django_filters.FilterSet):
        """API Filter for Articles"""
        # pylint: disable=too-few-public-methods
        authors = django_filters.CharFilter(name='authors__username')
        editors = django_filters.CharFilter(name='editors__username')
        tags = django_filters.CharFilter(name='tags__name')
        min_date = django_filters.DateFilter(name='pub_date', lookup_type='gte')
        max_date = django_filters.DateFilter(name='pub_date', lookup_type='lte')

        class Meta:
            model = Article
            fields = ('title', 'pub_date', 'min_date', 'max_date', 'authors', 'editors',
                      'foias', 'publish', 'tags')

    filter_class = Filter

    def get_queryset(self):
        if 'no_editor' in self.request.query_params:
            queryset = self.model.objects.filter(editors=None)
        else:
            queryset = self.model.objects.all()
        return queryset.prefetch_related('authors', 'editors', 'foias')
