"""
Views for the news application
"""

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.views.generic.list import ListView
from django.views.generic.dates import YearArchiveView, DateDetailView

from rest_framework import viewsets
from rest_framework.permissions import DjangoModelPermissions
import django_filters

from muckrock.news.models import Article
from muckrock.news.serializers import ArticleSerializer
from muckrock.settings import STRIPE_PUB_KEY
from muckrock.tags.models import Tag

# pylint: disable=too-many-ancestors

class NewsDetail(DateDetailView):
    """View for news detail"""
    date_field = 'pub_date'

    def get_queryset(self):
        """Get articles for this view"""
        if self.request.user.is_staff:
            return Article.objects.all()
        else:
            return Article.objects.get_published()

    def get_allow_future(self):
        """Can future posts be seen?"""
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super(NewsDetail, self).get_context_data(**kwargs)
        context['sidebar_admin_url'] = reverse('admin:news_article_change',
            args=(context['object'].pk,))
        context['stripe_pk'] = STRIPE_PUB_KEY
        return context

    def post(self, request, **kwargs):
        """Handles POST requests on article pages"""
        # pylint:disable=unused-argument
        tags = request.POST.get('tags')
        if tags:
            tag_set = set()
            for tag in tags.split(','):
                tag = Tag.normalize(tag)
                if not tag:
                    continue
                new_tag, _ = Tag.objects.get_or_create(name=tag)
                tag_set.add(new_tag)
            self.get_object().tags.set(*tag_set)
            self.get_object().save()
            messages.success(request, 'Your tags have been saved to this article.')
        return redirect(self.get_object())

class NewsYear(YearArchiveView):
    """View for year archive"""
    allow_empty = True
    date_field = 'pub_date'
    make_object_list = True
    queryset = Article.objects.get_published()


class List(ListView):
    """List of news articles"""
    paginate_by = 10
    queryset = Article.objects.get_published()


class ArticleViewSet(viewsets.ModelViewSet):
    """API views for Article"""
    # pylint: disable=too-many-ancestors
    # pylint: disable=too-many-public-methods
    model = Article
    serializer_class = ArticleSerializer
    permission_classes = (DjangoModelPermissions,)

    class Filter(django_filters.FilterSet):
        """API Filter for Articles"""
        # pylint: disable=no-member
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
        if 'no_editor' in self.request.QUERY_PARAMS:
            queryset = self.model.objects.filter(editors=None)
        else:
            queryset = self.model.objects.all()
        return queryset.prefetch_related('authors', 'editors', 'foias')
