"""
Views for the Agency application
"""

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.http import Http404
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext

from agency.forms import AgencyForm
from agency.models import Agency
from foia.models import FOIARequest
from jurisdiction.models import Jurisdiction
from jurisdiction.views import collect_stats, flag_helper

def detail(request, jurisdiction, slug, idx):
    """Details for an agency"""

    jmodel = get_object_or_404(Jurisdiction, slug=jurisdiction)
    agency = get_object_or_404(Agency, jurisdiction=jmodel, slug=slug, pk=idx)

    if not agency.approved:
        raise Http404()

    context = {'agency': agency}
    collect_stats(agency, context)

    return render_to_response('agency/agency_detail.html', context,
                              context_instance=RequestContext(request))

def list_(request):
    """List of popular agencies"""
    agencies = Agency.objects.annotate(num_requests=Count('foiarequest')) \
                             .order_by('-num_requests')[:10]
    context = {'agencies': agencies}

    return render_to_response('agency/agency_list.html', context,
                              context_instance=RequestContext(request))

@login_required
def update(request, jurisdiction, slug, idx):
    """Allow the user to fill in some information about new agencies they create"""

    jmodel = get_object_or_404(Jurisdiction, slug=jurisdiction)
    agency = get_object_or_404(Agency, jurisdiction=jmodel, slug=slug, pk=idx)

    if agency.user != request.user or agency.approved:
        messages.error(request, 'You may only edit your own agencies which have '
                                'not been approved yet')
        return redirect('foia-mylist', view='all')

    if request.method == 'POST':
        form = AgencyForm(request.POST, instance=agency)
        if form.is_valid():
            form.save()
            messages.success(request, 'Agency information saved.')
            foia_pk = request.GET.get('foia')
            foia = FOIARequest.objects.filter(pk=foia_pk)
            if foia:
                return redirect(foia[0])
            else:
                return redirect('foia-mylist', view='all')
    else:
        form = AgencyForm(instance=agency)

    return render_to_response('agency/agency_form.html', {'form': form},
                              context_instance=RequestContext(request))

@login_required
def flag(request, jurisdiction, slug, idx):
    """Flag a correction for an agency's information"""

    jmodel = get_object_or_404(Jurisdiction, slug=jurisdiction)
    agency = get_object_or_404(Agency, jurisdiction=jmodel, slug=slug, pk=idx)

    return flag_helper(request, agency, 'agency')
