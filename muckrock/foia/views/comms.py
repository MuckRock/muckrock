"""
Comm helper functions for FOIA views
"""

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.validators import ValidationError
from django.http import HttpResponse, Http404
from django.shortcuts import redirect, get_object_or_404

from datetime import datetime

from muckrock.communication.utils import get_email_or_fax
from muckrock.foia.models import FOIACommunication, STATUS

def save_foia_comm(foia, from_user, comm, user, appeal=False,
        snail=False, thanks=False, subject=''):
    """Save the FOI Communication"""
    #pylint:disable=too-many-arguments
    FOIACommunication.objects.create(
        foia=foia,
        from_user=from_user,
        to_user=foia.get_to_user(),
        date=datetime.now(),
        response=False,
        full_html=False,
        communication=comm,
        thanks=thanks,
        subject=subject,
    )
    foia.communications.update()
    foia.process_attachments(user)
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
        if request.POST['email_or_fax']:
            email_or_fax = get_email_or_fax(request.POST['email_or_fax'])
        else:
            email_or_fax = None
        comm.resend(email_or_fax)
        messages.success(request, 'The communication was resent.')
    except (KeyError, FOIACommunication.DoesNotExist):
        messages.error(request, 'The communication does not exist.')
    except ValidationError:
        messages.error(request, 'The provided email or fax was invalid')
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
    raw_email = comm.get_raw_email()
    if raw_email:
        return HttpResponse(
                raw_email.raw_email,
                content_type='text/plain; charset=utf-8',
                )
    else:
        raise Http404
