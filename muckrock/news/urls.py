"""
URL mappings for the News application
"""

from django.conf.urls.defaults import patterns, url
from django.views.generic import list_detail, date_based

from news import views
from news.models import Article
from news.feeds import LatestEntries

article_args = {'queryset': Article.objects.get_published()}
article_date_list_args = dict(article_args, date_field='pub_date', allow_empty=True)

years = [date.year for date in Article.objects.dates('pub_date', 'year')][::-1]

urlpatterns = patterns('',
        url(r'^$', date_based.archive_index, dict(article_date_list_args, num_latest=5),
            name='news-index'),
        url(r'^archives/$', list_detail.object_list,
            dict(article_args, paginate_by=10, extra_context={'years': years}),
            name='news-archive'),
        url(r'^archives/(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/(?P<slug>[-\w\d]+)/$',
            views.news_detail, name='news-detail'),
        url(r'^archives/(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/$',
            date_based.archive_day, article_date_list_args, name='news-archive-day'),
        url(r'^archives/(?P<year>\d{4})/(?P<month>[a-z]{3})/$',
            date_based.archive_month, article_date_list_args, name='news-archive-month'),
        url(r'^archives/(?P<year>\d{4})/$',
            views.news_year, dict(article_date_list_args, make_object_list=True),
            name='news-archive-year'),
        url(r'^feeds/$', LatestEntries(), name='news-feed'),
)
