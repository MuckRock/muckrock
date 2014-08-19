"""
Views for the news application
"""

from django.views.generic.list import ListView
from django.views.generic.dates import YearArchiveView, DateDetailView

from rest_framework import viewsets
from rest_framework.permissions import DjangoModelPermissions
import django_filters

from muckrock.news.models import Article
from muckrock.news.serializers import ArticleSerializer
from muckrock.sidebar.models import Sidebar

# pylint: disable=R0901

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
        if self.request.user.is_anonymous():
            context['sidebar'] = Sidebar.objects.get_text('anon_article')
        else:
            context['sidebar'] = Sidebar.objects.get_text('article')
        return context


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

    def get_context_data(self, **kwargs):
        context = super(List, self).get_context_data(**kwargs)
        context['years'] = [date.year for date in Article.objects.dates('pub_date', 'year')][::-1]
        return context


class ArticleViewSet(viewsets.ModelViewSet):
    """API views for User"""
    # pylint: disable=R0901
    # pylint: disable=R0904
    model = Article
    serializer_class = ArticleSerializer
    permission_classes = (DjangoModelPermissions,)

    class Filter(django_filters.FilterSet):
        """API Filter for Articles"""
        # pylint: disable=E1101
        # pylint: disable=R0903
        authors = django_filters.CharFilter(name='authors__username')
        tags = django_filters.CharFilter(name='tags__name')

        class Meta:
            model = Article
            fields = ('title', 'pub_date', 'authors', 'foias', 'tags')

    filter_class = Filter
