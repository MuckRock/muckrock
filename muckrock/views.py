"""
Views for muckrock project
"""

from django.db.models import Sum
from django.http import HttpResponseServerError
from django.shortcuts import render_to_response
from django.template import RequestContext, Context, loader

from foia.models import FOIARequest, FOIADocument
from news.models import Article

def front_page(request):
    """Get all the details needed for the front page"""
    # pylint: disable=W0612
    # pylint: disable=E1103

    try:
        featured_article = Article.objects.get_published()[0]
    except IndexError:
        # no published articles
        featured_article = None

    featured_reqs = FOIARequest.objects.get_public().filter(featured=True)\
                                       .order_by('-date_done')[:3]

    num_requests = FOIARequest.objects.exclude(status='started').count()
    num_completed_requests = FOIARequest.objects.filter(status='done').count()
    num_denied_requests = FOIARequest.objects.filter(status='rejected').count()
    num_pages = FOIADocument.objects.aggregate(Sum('pages'))['pages__sum']

    most_viewed_reqs = FOIARequest.objects.order_by('-times_viewed')[:5]
    recent_articles = Article.objects.get_published()[:5]
    overdue_requests = FOIARequest.objects.get_overdue().get_public()[:5]

    return render_to_response('front_page.html', locals(),
                              context_instance=RequestContext(request))

def handler500(request):
    """
    500 error handler which includes ``request`` in the context.

    Templates: `500.html`
    Context: None
    """

    template = loader.get_template('500.html')
    return HttpResponseServerError(template.render(Context({'request': request})))
