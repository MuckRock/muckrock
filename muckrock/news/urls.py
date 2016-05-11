"""
URL mappings for the News application
"""

from django.conf.urls import patterns, url
from django.views.generic.base import RedirectView
from django.views.generic.dates import DayArchiveView, MonthArchiveView

from muckrock.news import views
from muckrock.news.models import Article
from muckrock.news.feeds import LatestEntries

# pylint: disable=no-value-for-parameter

article_args = {'queryset': Article.objects.get_published()}
article_date_list_args = dict(article_args, date_field='pub_date', allow_empty=True)

urlpatterns = patterns(
    '',
    url(
        r'^$',
        RedirectView.as_view(url='/news/archives/'),
        name='news-index'
    ),
    url(
        r'^archives/$',
        views.List.as_view(template_name='lists/news_list.html'),
        name='news-archive'
    ),
    url(
        r'^archives/(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/(?P<slug>[-\w\d]+)/$',
        views.NewsDetail.as_view(template_name='details/news_detail.html'),
        name='news-detail'
    ),
    url(
        r'^archives/(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/$',
        DayArchiveView.as_view(
            template_name='archives/day_archive.html',
            **article_date_list_args),
        name='news-archive-day'
    ),
    url(
        r'^archives/(?P<year>\d{4})/(?P<month>[a-z]{3})/$',
        MonthArchiveView.as_view(
            template_name='archives/month_archive.html',
            **article_date_list_args),
        name='news-archive-month'
    ),
    url(
        r'^archives/(?P<year>\d{4})/$',
        views.NewsYear.as_view(template_name='archives/year_archive.html'),
        name='news-archive-year'
    ),
    url(r'^author/(?P<username>[\w\-.@ ]+)/$',
        views.AuthorArchiveView.as_view(),
        name='news-author'
    ),
    url(
        r'^feeds/$',
        LatestEntries(),
        name='news-feed'
    ),
)
