"""
URL mappings for the News application
"""

from django.conf.urls.defaults import patterns, url
from django.views.generic import list_detail, date_based

from news.models import Article

article_args = {'queryset': Article.objects.get_published()}
article_date_args = dict(article_args, date_field='pub_date')
article_date_list_args = dict(article_date_args, allow_empty=True)

urlpatterns = patterns('',
        url(r'^$', list_detail.object_list, dict(article_args, paginate_by=5), name='news-index'),
        url(r'^(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/(?P<slug>[-\w\d]+)/$',
            date_based.object_detail, article_date_args, name='news-detail'),
        url(r'^(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/$',
            date_based.archive_day, article_date_list_args),
        url(r'^(?P<year>\d{4})/(?P<month>[a-z]{3})/$',
            date_based.archive_month, article_date_list_args),
        url(r'^(?P<year>\d{4})/$',
            date_based.archive_year, dict(article_date_list_args, make_object_list=True)),
)
