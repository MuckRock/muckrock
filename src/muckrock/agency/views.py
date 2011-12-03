"""
Views for the Agency application
"""

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext

from agency.forms import AgencyForm
from agency.models import Agency
from foia.models import FOIARequest

@login_required
def update(request, idx):
    """Allow the user to fill in some information about new agencies they create"""

    agency = get_object_or_404(Agency, pk=idx)

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
