"""
Views for muckrock project
"""

from django.db.models import Sum
from django.shortcuts import render_to_response
from django.template import RequestContext

from foia.models import FOIARequest, FOIADocument, FOIADocTopViewed
from news.models import Article

def front_page(request):
    """Get all the details needed for the front page"""
    # pylint: disable-msg=W0612

    featured_article = Article.objects.all()[0]
    featured_reqs = FOIARequest.objects.filter(featured=True).order_by('-date_done')[:3]

    num_requests = FOIARequest.objects.count()
    num_completed_requests = FOIARequest.objects.filter(status='done').count()
    num_denied_requests = FOIARequest.objects.filter(status='rejected').count()
    num_pages = FOIADocument.objects.aggregate(Sum('pages'))['pages__sum']

    most_viewed_docs = [tv.doc for tv in FOIADocTopViewed.objects.select_related(depth=1).all()[:5]]
    recent_articles = Article.objects.all()[:5]
    overdue_requests = FOIARequest.objects.get_overdue()[:5]

    return render_to_response('front_page.html', locals(),
                              context_instance=RequestContext(request))
