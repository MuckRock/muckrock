"""
Comm helper functions for FOIA views
"""

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.validators import ValidationError
from django.http import HttpResponse, Http404
from django.shortcuts import redirect, get_object_or_404

from datetime import datetime

from muckrock.foia.models import FOIACommunication, STATUS

def save_foia_comm(foia, from_user, comm_text,
        formset=None, appeal=False, snail=False, thanks=False):
    """Save the FOI Communication"""
    #pylint:disable=too-many-arguments
    comm = FOIACommunication.objects.create(
        foia=foia,
        from_user=from_user,
        to_user=foia.contact,
        date=datetime.now(),
        response=False,
        communication=comm_text,
        thanks=thanks,
    )
    if formset is not None:
        foia_files = formset.save(commit=False)
        for foia_file in foia_files:
            foia_file.comm = comm
            foia_file.title = foia_file.name()
            foia_file.date = comm.date
            foia_file.save()
    foia.submit(appeal=appeal, snail=snail, thanks=thanks)

@user_passes_test(lambda u: u.is_staff)
def move_comm(request, next_):
    """Admin moves a communication to a different FOIA"""
    try:
        comm_pk = request.POST['comm_pk']
        comm = FOIACommunication.objects.get(pk=comm_pk)
        new_foia_pks = request.POST['new_foia_pks'].split(',')
        comm.move(new_foia_pks)
        msg = 'Communication moved successfully'
        messages.success(request, msg)
    except (KeyError, FOIACommunication.DoesNotExist):
        messages.error(request, 'The communication does not exist.')
    except ValueError:
        messages.error(request, 'No move destination provided.')
    return redirect(next_)

@user_passes_test(lambda u: u.is_staff)
def delete_comm(request, next_):
    """Admin deletes a communication"""
    try:
        comm = FOIACommunication.objects.get(pk=request.POST['comm_pk'])
        files = comm.files.all()
        for file_ in files:
            file_.delete()
        comm.delete()
        messages.success(request, 'The communication was deleted.')
    except (KeyError, FOIACommunication.DoesNotExist):
        messages.error(request, 'The communication does not exist.')
    return redirect(next_)

@user_passes_test(lambda u: u.is_staff)
def resend_comm(request, next_):
    """Resend the FOI Communication"""
    try:
        comm = FOIACommunication.objects.get(pk=request.POST['comm_pk'])
        comm.resend(request.POST['email'])
        messages.success(request, 'The communication was resent.')
    except (KeyError, FOIACommunication.DoesNotExist):
        messages.error(request, 'The communication does not exist.')
    except ValidationError:
        messages.error(request, 'The provided email was invalid')
    except ValueError as exc:
        if exc.args[1] == 'no_foia':
            messages.error(request, 'The communication is an orphan and cannot be resent.')
        elif exc.args[1] == 'no_agency':
            messages.error(request, 'The communication\'s associated agency is '
                    'not approved, refusing to resend.')
    return redirect(next_)

@user_passes_test(lambda u: u.is_staff)
def change_comm_status(request, next_):
    """Change the status of a communication"""
    try:
        comm = FOIACommunication.objects.get(pk=request.POST['comm_pk'])
        status = request.POST.get('status', '')
        if status in [s for s, _ in STATUS]:
            comm.status = status
            comm.save()
    except (KeyError, FOIACommunication.DoesNotExist):
        messages.error(request, 'The communication does not exist.')
    return redirect(next_)

@user_passes_test(lambda u: u.is_authenticated() and u.profile.is_advanced())
def raw(request, idx):
    """Get the raw email for a communication"""
    # pylint: disable=unused-argument
    comm = get_object_or_404(FOIACommunication, pk=idx)
    if not comm.rawemail:
        raise Http404()
    return HttpResponse(comm.rawemail.raw_email, content_type='text/plain')
