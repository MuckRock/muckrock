"""
Views for the news application
"""

from django.views.generic import date_based

from news.models import Article

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
