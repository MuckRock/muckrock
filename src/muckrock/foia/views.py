"""
Views for the FOIA application
"""

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic import list_detail

from datetime import datetime

from foia.forms import FOIARequestForm
from foia.models import FOIARequest

def _foia_form_handler(request, foia, action):
    """Handle a form for a FOIA request - user to create and update a FOIA request"""

    if request.method == 'POST':
        status_dict = {'Submit': 'submitted', 'Save': 'started'}
        foia.date_submitted = datetime.now() if request.POST['submit'] == 'Submit' else None
        foia.status = status_dict[request.POST['submit']],

        form = FOIARequestForm(request.POST, instance=foia)

        if form.is_valid():
            foia_request = form.save()

            return HttpResponseRedirect('/foia/view/%s/' % foia_request.pk)

    else:
        form = FOIARequestForm(instance=foia)

    return render_to_response('foia/foiarequest_form.html',
                              {'form': form, 'action': action},
                              context_instance=RequestContext(request))

@login_required
def create_foiarequest(request):
    """File a new FOIA Request"""

    foia = FOIARequest(user = request.user)
    return _foia_form_handler(request, foia, 'New')

@login_required
def update_foiarequest(request, object_id):
    """Update a started FOIA Request"""

    foia = get_object_or_404(FOIARequest, pk=object_id)

    if not foia.is_editable():
        return render_to_response('error.html',
                 {'message': 'You may only edit non-submitted requests unless a fix is requested'},
                 context_instance=RequestContext(request))
    if foia.user != request.user:
        return render_to_response('error.html',
                 {'message': 'You may only edit your own requests'},
                 context_instance=RequestContext(request))

    return _foia_form_handler(request, foia, 'Update')

def list_by_user(request, user_name):
    """List of all FOIA requests by a given user"""

    user = User.objects.get(username=user_name)
    return list_detail.object_list(request, FOIARequest.objects.filter(user=user))

