"""
Views for the news application
"""

from django.views.generic.list import ListView
from django.views.generic.dates import YearArchiveView, DateDetailView

from muckrock.news.models import Article

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


class NewsYear(YearArchiveView):
    """View for year archive"""
    allow_empty = True
    date_field = 'pub_date'
    make_object_list = True
    queryset = Article.objects.get_published()

    def get_context_data(self, **kwargs):
        context = super(NewsYear, self).get_context_data(**kwargs)
        year = int(self.kwargs['year'])
        if year > 1000:
            context['prev_year'] = year - 1
        if year < 9999:
            context['next_year'] = year + 1
        return context


class List(ListView):
    """List of news articles"""
    paginate_by = 10
    queryset = Article.objects.get_published()

    def get_context_data(self, **kwargs):
        context = super(List, self).get_context_data(**kwargs)
        context['years'] = [date.year for date in Article.objects.dates('pub_date', 'year')][::-1]
        return context
