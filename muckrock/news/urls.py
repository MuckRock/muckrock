"""
URL mappings for the News application
"""

# Django
from django.conf.urls import url

# MuckRock
from muckrock.news import views
from muckrock.news.feeds import LatestEntries
from muckrock.news.models import Article

# pylint: disable=no-value-for-parameter

article_args = {'queryset': Article.objects.get_published()}
article_date_list_args = dict(
    article_args, date_field='pub_date', allow_empty=True
)

urlpatterns = [
    url(r'^$', views.NewsExploreView.as_view(), name='news-index'),
    url(r'^archives/$', views.NewsListView.as_view(), name='news-archive'),
    url(
        r'^archives/(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/(?P<slug>[-\w\d]+)/$',
        views.NewsDetail.as_view(),
        name='news-detail'
    ),
    url(
        r'^archives/(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/$',
        views.NewsDay.as_view(),
        name='news-archive-day'
    ),
    url(
        r'^archives/(?P<year>\d{4})/(?P<month>[a-z]{3})/$',
        views.NewsMonth.as_view(),
        name='news-archive-month'
    ),
    url(
        r'^archives/(?P<year>\d{4})/$',
        views.NewsYear.as_view(),
        name='news-archive-year'
    ),
    url(
        r'^author/(?P<username>[\w\-.@ ]+)/$',
        views.AuthorArchiveView.as_view(),
        name='news-author'
    ),
    url(r'^feeds/$', LatestEntries(), name='news-feed'),
]
