"""
Views for muckrock project
"""
from django.contrib import messages
from django.db.models import Sum
from django.http import HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext, Context, loader
from django.utils.decorators import method_decorator

from muckrock.foia.models import FOIARequest, FOIAFile
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.news.models import Article

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
    num_pages = FOIAFile.objects.aggregate(Sum('pages'))['pages__sum']

    most_viewed_reqs = FOIARequest.objects.order_by('-times_viewed')[:5]
    recent_articles = Article.objects.get_published()[:5]
    overdue_requests = FOIARequest.objects.get_overdue().get_public()[:5]

    return render_to_response('front_page.html', locals(),
                              context_instance=RequestContext(request))

def blog(request, path=''):
    """Redirect to the new blog URL"""
    # pylint: disable=W0613
    return redirect('http://blog.muckrock.com/%s/' % path, permanant=True)

def jurisdiction(request, jurisdiction=None, slug=None, idx=None, view=None):
    """Redirect to the jurisdiction page"""
    # pylint: disable=W0621
    # pylint: disable=W0613

    if jurisdiction and idx:
        jmodel = get_object_or_404(Jurisdiction, slug=jurisdiction, pk=idx)
    if idx:
        jmodel = get_object_or_404(Jurisdiction, pk=idx)

    if not view:
        return redirect(jmodel)
    else:
        return redirect(jmodel.get_url(view))

def handler500(request):
    """
    500 error handler which includes ``request`` in the context.

    Templates: `500.html`
    Context: None
    """

    template = loader.get_template('500.html')
    return HttpResponseServerError(template.render(Context({'request': request})))


# http://stackoverflow.com/a/8429311
def class_view_decorator(function_decorator):
    """Convert a function based decorator into a class based decorator usable
    on class based Views.

    Can't subclass the `view` as it breaks inheritance (super in particular),
    so we monkey-patch instead.
    """

    def simple_decorator(view):
        """Wrap the dispatch method"""
        view.dispatch = method_decorator(function_decorator)(view.dispatch)
        return view

    return simple_decorator
