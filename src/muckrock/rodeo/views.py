"""
Views for the Rodeo application
"""

from django.contrib import messages
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

from foia.models import FOIADocument
from rodeo.models import Rodeo
from rodeo.forms import RodeoVoteForm

def main(request, doc_id, rodeo_pk):
    """The main rodeo request page"""

    doc = get_object_or_404(FOIADocument, doc_id=doc_id)
    rodeo = get_object_or_404(Rodeo, document=doc, pk=rodeo_pk)

    if not doc.is_viewable(request.user) or not doc.doc_id:
        raise Http404()

    if request.method == 'POST':
        page = int(request.POST.get('page', rodeo.random_page()))
        form = RodeoVoteForm(request.POST, rodeo=rodeo)
        if form.is_valid():
            vote = form.save(commit=False)
            if request.user.is_authenticated():
                vote.user = request.user
            vote.save()
            messages.info(request, 'Your vote has been recorded')
            return HttpResponseRedirect(rodeo.get_absolute_url())
    else:
        page = rodeo.random_page()
        form = RodeoVoteForm(rodeo=rodeo, initial={'page': page})

    return render_to_response('rodeo/rodeo_detail.html',
                              {'form': form, 'page': page, 'rodeo': rodeo,
                               'img': rodeo.document.get_thumbnail('normal', page)},
                              context_instance=RequestContext(request))
