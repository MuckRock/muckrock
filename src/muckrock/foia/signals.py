"""Model signal handlers for the FOIA applicaiton"""

from django.core.mail import send_mail
from django.db.models.signals import pre_save
from django.template.loader import render_to_string

from foia.models import FOIARequest
from foia.tasks import upload_document_cloud

def foia_email_notifier(sender, **kwargs):
    """Log changes to FOIA Requests"""
    # pylint: disable-msg=W0613

    request = kwargs['instance']
    try:
        old_request = FOIARequest.objects.get(pk=request.pk)
    except FOIARequest.DoesNotExist:
        # if we are saving a new FOIA Request, do not email them
        return

    if request.status != old_request.status and \
            request.status not in ['started', 'submitted']:
        msg = render_to_string('foia/mail.txt',
            {'name': request.user.get_full_name(),
             'title': request.title,
             'status': request.get_status_display(),
             'link': request.get_absolute_url()})
        send_mail('[MuckRock] FOIA request has been updated',
                  msg, 'info@muckrock.com', [request.user.email], fail_silently=False)
    if request.status == 'submitted':
        send_mail('[NEW] Freedom of Information Request: %s' % request.title,
                  render_to_string('foia/admin_mail.txt', {'request': request}),
                  'info@muckrock.com', ['requests@muckrock.com'], fail_silently=False)

def foia_update_embargo(sender, **kwargs):
    """When embargo has possibly been switched, update the document cloud permissions"""
    # pylint: disable-msg=E1101
    # pylint: disable-msg=W0613

    request = kwargs['instance']
    try:
        old_request = FOIARequest.objects.get(pk=request.pk)
    except FOIARequest.DoesNotExist:
        # if we are saving a new FOIA Request, there are no docs to update
        return

    if request.is_embargo() != old_request.is_embargo():
        access = 'private' if request.is_embargo() else 'public'
        for doc in request.documents.all():
            if doc.access != access:
                doc.access = access
                doc.save()
                upload_document_cloud.apply_async(args=[doc.pk, True], countdown=3)

pre_save.connect(foia_email_notifier, sender=FOIARequest, dispatch_uid='muckrock.foia.signals')
pre_save.connect(foia_update_embargo, sender=FOIARequest, dispatch_uid='muckrock.foia.signals')

