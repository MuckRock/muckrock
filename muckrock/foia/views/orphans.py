"""
Views for the FOIA application that deal with orphan requests
"""

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext

from muckrock.foia.models import FOIACommunication
from muckrock.foia.views.comms import move_comm, delete_comm

@user_passes_test(lambda u: u.is_staff)
def _delete_selected(request, next_):
    """Admin deletes multiple communications"""
    comm_pks = request.POST.getlist('comm_pks')
    for comm_pk in comm_pks:
        try:
            comm = FOIACommunication.objects.get(pk=comm_pk)
            files = comm.files.all()
            for file_ in files:
                file_.delete()
            comm.delete()
            messages.success(request, 'Communication %s deleted' % comm_pk)
        except (KeyError, FOIACommunication.DoesNotExist):
            continue
    return redirect(next_)

@user_passes_test(lambda u: u.is_staff)
def orphans(request):
    """Display all orphaned communications"""
    if request.method == 'POST':
        actions = {
            'move_comm': move_comm,
            'delete_comm': delete_comm,
            'delete_selected': _delete_selected,
        }
        try:
            return actions[request.POST['action']](request, 'foia-orphans')
        except KeyError: # if submitting form from web page improperly
            return redirect('foia-orphans')
    elif 'comm_id' in request.GET:
        communications = FOIACommunication.objects.filter(foia=None, pk=request.GET['comm_id'])
        return render_to_response('staff/orphans.html',
                                  {'communications': communications},
                                  context_instance=RequestContext(request))
    else:
        communications = FOIACommunication.objects.filter(foia=None)
        paginator = Paginator(communications, 25)
        try:
            page = paginator.page(request.GET.get('page'))
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)
        return render_to_response(
            'staff/orphans.html',
            {'communications': page},
            context_instance=RequestContext(request)
        )
