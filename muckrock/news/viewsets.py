"""
Viewsets for the news application API
"""

# Third Party
import django_filters
from rest_framework import viewsets
from rest_framework.permissions import DjangoModelPermissions

# MuckRock
from muckrock.news.models import Article, Photo
from muckrock.news.serializers import ArticleSerializer, PhotoSerializer


class ArticleViewSet(viewsets.ModelViewSet):
    """API views for Article"""
    model = Article
    serializer_class = ArticleSerializer
    permission_classes = (DjangoModelPermissions,)

    class Filter(django_filters.FilterSet):
        """API Filter for Articles"""
        authors = django_filters.CharFilter(name='authors__username')
        editors = django_filters.CharFilter(name='editors__username')
        foias = django_filters.NumberFilter(name='foias__id')
        tags = django_filters.CharFilter(name='tags__name')
        min_date = django_filters.DateFilter(name='pub_date', lookup_expr='gte')
        max_date = django_filters.DateFilter(name='pub_date', lookup_expr='lte')

        class Meta:
            model = Article
            fields = (
                'title',
                'pub_date',
                'min_date',
                'max_date',
                'authors',
                'editors',
                'foias',
                'publish',
            )

    filter_class = Filter

    def get_queryset(self):
        if 'no_editor' in self.request.query_params:
            queryset = self.model.objects.filter(editors=None)
        else:
            queryset = self.model.objects.all()
        return queryset.prefetch_related('authors', 'editors', 'foias')


class PhotoViewSet(viewsets.ModelViewSet):
    """API views for Photo"""
    model = Photo
    serializer_class = PhotoSerializer
    permission_classes = (DjangoModelPermissions,)
    queryset = Photo.objects.order_by('image')
