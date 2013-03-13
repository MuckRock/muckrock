"""
Views for the news application
"""

from django.views.generic import date_based

from muckrock.news.models import Article

def news_detail(request, year, month, day, slug):
    """View for news detail"""

    if request.user.is_staff:
        queryset = Article.objects.all()
        allow_future = True
    else:
        queryset = Article.objects.get_published()
        allow_future = False

    return date_based.object_detail(request, year, month, day, queryset, 'pub_date',
                                    slug=slug, allow_future=allow_future)

def news_year(request, **kwargs):
    """View for year archive"""
    year = int(kwargs['year'])
    extra_context = {}
    if year > 1000:
        extra_context['prev_year'] = year - 1
    if year < 9999:
        extra_context['next_year'] = year + 1
    return date_based.archive_year(request, extra_context=extra_context, **kwargs)
