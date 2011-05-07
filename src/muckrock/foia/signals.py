"""Model signal handlers for the FOIA applicaiton"""

from django.db.models.signals import pre_save

from foia.models import FOIARequest
from foia.tasks import upload_document_cloud

def foia_update_embargo(sender, **kwargs):
    """When embargo has possibly been switched, update the document cloud permissions"""
    # pylint: disable-msg=E1101
    # pylint: disable-msg=W0613

    request = kwargs['instance']
    old_request = request.get_saved()

    if not old_request:
        # if we are saving a new FOIA Request, there are no docs to update
        return

    if request.is_embargo(save=False) != old_request.is_embargo(save=False):
        access = 'private' if request.is_embargo(save=False) else 'public'
        for doc in request.documents.all():
            if doc.access != access:
                doc.access = access
                doc.save()
                upload_document_cloud.apply_async(args=[doc.pk, True], countdown=3)

pre_save.connect(foia_update_embargo, sender=FOIARequest,
                 dispatch_uid='muckrock.foia.signals.embargo')

