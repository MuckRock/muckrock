"""
Views for the Jurisdiction application
"""

from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

from jurisdiction.models import Jurisdiction

def collect_stats(obj, context):
    """Helper for collecting stats"""
    for status in ['rejected', 'processed', 'fix', 'no_docs', 'done', 'appealing']:
        context['num_%s' % status] = obj.foiarequest_set.filter(status=status).count()
    context['num_overdue'] = obj.foiarequest_set.get_overdue().count()
    context['num_submitted'] = obj.foiarequest_set.get_submitted().count()
    context['submitted_reqs'] = obj.foiarequest_set.get_public().order_by('-date_submitted')[:5]
    context['overdue_reqs'] = obj.foiarequest_set.get_public() \
                                 .get_overdue().order_by('date_due')[:5]

def detail(request, slug, idx):
    """Details for a jurisdiction"""

    jurisdiction = get_object_or_404(Jurisdiction, slug=slug, pk=idx)
    context = {'jurisdiction': jurisdiction}
    collect_stats(jurisdiction, context)

    return render_to_response('jurisdiction/jurisdiction_detail.html', context,
                              context_instance=RequestContext(request))
