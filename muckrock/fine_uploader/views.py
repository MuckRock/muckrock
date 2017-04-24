"""Views to interact with Fine Uploader AJAX calls"""

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.http import (
        HttpResponse,
        JsonResponse,
        HttpResponseBadRequest,
        HttpResponseForbidden,
        )

from datetime import datetime
import base64
import hashlib
import hmac
import json

from muckrock.foia.models import (
        FOIARequest,
        OutboundAttachment,
        )


@login_required
def success(request):
    """"File has been succesfully uploaded"""
    try:
        foia = FOIARequest.objects.get(pk=request.POST.get('foia_id'))
    except FOIARequest.DoesNotExist:
        return HttpResponseBadRequest()
    if not foia.has_perm(request.user, 'change'):
        return HttpResponseForbidden()
    if 'key' not in request.POST:
        return HttpResponseBadRequest()

    attachment = OutboundAttachment(
            foia=foia,
            user=request.user,
            date_time_stamp=datetime.now(),
            )
    attachment.ffile.name = request.POST['key']
    attachment.save()

    return HttpResponse()


@login_required
def session(request):
    """"Get the initial file list"""
    try:
        foia = FOIARequest.objects.get(pk=request.GET.get('foia_id'))
    except FOIARequest.DoesNotExist:
        return HttpResponseBadRequest()
    if not foia.has_perm(request.user, 'change'):
        return HttpResponseForbidden()

    attms = foia.pending_attachments.filter(user=request.user, sent=False)

    data = []
    for attm in attms:
        data.append({
            'name': attm.name(),
            'uuid': attm.pk,
            'size': attm.ffile.size,
            's3Key': attm.ffile.name,
            })
    return JsonResponse(data, safe=False)


@login_required
def delete(request):
    """Delete a file"""
    try:
        attm = OutboundAttachment.objects.get(
                ffile=request.POST.get('key'),
                user=request.user,
                sent=False,
                )
    except OutboundAttachment.DoesNotExist:
        return HttpResponseBadRequest()

    if not attm.foia.has_perm(request.user, 'change'):
        return HttpResponseForbidden()

    attm.delete()
    return HttpResponse()


@login_required
def sign(request):
    """Sign the data to upload to S3"""
    payload = json.loads(request.body)
    if 'headers' in payload:
        return JsonResponse(_sign_headers(payload['headers']))
    elif _is_valid_policy(request.user, payload):
        return JsonResponse(_sign_policy_document(payload))
    else:
        return JsonResponse({'invalid': True}, status=400)


def _is_valid_policy(user, policy_document):
    """
    Verify the policy document has not been tampered with client-side
    before sending it off.
    """
    bucket = None
    parsed_max_size = None

    if user.profile.acct_type in ('admin', 'agency'):
        max_size = None
    else:
        max_size = settings.MAX_ATTACHMENT_SIZE

    for condition in policy_document['conditions']:
        if isinstance(condition, list) and condition[0] == 'content-length-range':
            parsed_max_size = int(condition[2])
        elif 'bucket' in condition:
            bucket = condition['bucket']

    return (bucket == settings.AWS_STORAGE_BUCKET_NAME and
            parsed_max_size == max_size)


def _sign_policy_document(policy_document):
    """Sign and return the policy doucument for a simple upload.
    http://aws.amazon.com/articles/1434/#signyours3postform"""
    policy = base64.b64encode(json.dumps(policy_document))
    signature = base64.b64encode(hmac.new(
        settings.AWS_SECRET_ACCESS_KEY,
        policy,
        hashlib.sha1,
        ).digest())
    return {
        'policy': policy,
        'signature': signature
    }


def _sign_headers(headers):
    """Sign and return the headers for a chunked upload"""
    return {
        'signature': base64.b64encode(hmac.new(
            settings.AWS_SECRET_ACCESS_KEY,
            headers,
            hashlib.sha1,
            ).digest())
    }


@login_required
def key_name(request):
    """Generate the S3 key name from the filename"""
    name = request.POST.get('name')
    foia_id = request.POST.get('foia_id')
    attachment = OutboundAttachment(
            user=request.user,
            foia_id=foia_id,
            )
    key = attachment.ffile.field.generate_filename(
            attachment.ffile.instance,
            name,
            )
    key = default_storage.get_available_name(key)
    return JsonResponse({'key': key})


@login_required
def blank(request):
    """Workaround for IE9 and older"""
    # pylint: disable=unused-argument
    return HttpResponse()
