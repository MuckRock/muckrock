"""
Comm helper functions for FOIA views
"""

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.files.base import ContentFile
from django.core.validators import validate_email, ValidationError
from django.shortcuts import redirect

from datetime import datetime

from muckrock.foia.models import FOIARequest, FOIACommunication

# pylint: disable=too-many-arguments
def save_foia_comm(request, foia, from_who, comm, message, formset=None, appeal=False, snail=False):
    """Save the FOI Communication"""
    comm = FOIACommunication.objects.create(
        foia=foia,
        from_who=from_who,
        to_who=foia.get_to_who(),
        date=datetime.now(),
        response=False,
        full_html=False,
        communication=comm
    )
    if formset is not None:
        foia_files = formset.save(commit=False)
        for foia_file in foia_files:
            foia_file.comm = comm
            foia_file.title = foia_file.name()
            foia_file.date = comm.date
            foia_file.save()
    foia.submit(appeal=appeal, snail=snail)
    messages.success(request, message)

@user_passes_test(lambda u: u.is_staff)
def move_comm(request, next_):
    """Admin moves a communication to a different FOIA"""
    try:
        comm_pk = request.POST['comm_pk']
        comm = FOIACommunication.objects.get(pk=comm_pk)
    except (KeyError, FOIACommunication.DoesNotExist):
        messages.error(request, 'The communication does not exist.')
        return redirect(next_)

    files = comm.files.all()
    new_foia_pks = request.POST['new_foia_pk_%s' % comm_pk].split(',')
    new_foias = []
    for new_foia_pk in new_foia_pks:
        # setting pk to none clones the request to a new entry in the db
        try:
            new_foia = FOIARequest.objects.get(pk=new_foia_pk)
        except (FOIARequest.DoesNotExist, ValueError):
            messages.error(request, 'FOIA %s does not exist' % new_foia_pk)
            continue
        new_foias.append(new_foia)
        comm.pk = None
        comm.foia = new_foia
        comm.save()
        for file_ in files:
            file_.pk = None
            file_.foia = new_foia
            file_.comm = comm
            # make a copy of the file on the storage backend
            new_ffile = ContentFile(file_.ffile.read())
            new_ffile.name = file_.ffile.name
            file_.ffile = new_ffile
            file_.save()
            upload_document_cloud.apply_async(args=[file_.pk, False], countdown=3)
    if not new_foias:
        messages.error(request, 'No valid FOIA requests given')
        return redirect(next_)
    comm = FOIACommunication.objects.get(pk=request.POST['comm_pk'])
    comm.delete()
    msg = 'Communication moved to the following requests:<br>'
    href = lambda f: '<a href="%s">%s</a>' % (f.get_absolute_url(), f.pk)
    msg += '<br>'.join(href(f) for f in new_foias)
    messages.success(request, msg)
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
        comm.date = datetime.now()
        comm.save()
        foia = comm.foia
        email = request.POST['email']
        if email:
            validate_email(email)
            foia.email = email
            foia.save()
            snail = False
        else:
            snail = True
        foia.submit(snail=snail)
        messages.success(request, 'The communication was resent.')
    except (KeyError, FOIACommunication.DoesNotExist):
        messages.error(request, 'The communication does not exist.')
    except ValidationError:
        messages.error(request, 'Not a valid email address')
    return redirect(next_)
