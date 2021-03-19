"""Views to interact with Fine Uploader AJAX calls"""

# Django
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    JsonResponse,
)
from django.utils import timezone

# Standard Library
import base64
import hashlib
import hmac
import json
import os
from functools import wraps

# MuckRock
from muckrock.foia.models import (
    FOIACommunication,
    FOIAComposer,
    FOIAFile,
    FOIARequest,
    OutboundComposerAttachment,
    OutboundRequestAttachment,
)


def login_or_agency_required(function):
    """Allow semi-authenticated agency users to upload files"""

    @wraps(function)
    def wrapper(request, *args, **kwargs):
        """If the user has a valid passcode for the request, treat them as the
        agency user for this view
        """
        if not request.user.is_authenticated:
            try:
                if request.method == "POST":
                    data = request.POST
                else:
                    data = request.GET
                foia = FOIARequest.objects.get(pk=data["id"])
            except (FOIARequest.DoesNotExist, KeyError):
                return HttpResponseForbidden()
            if request.session.get(f"foiapasscode:{foia.pk}"):
                request.user = foia.agency.get_user()
            else:
                return HttpResponseForbidden()

        return function(request, *args, **kwargs)

    return wrapper


def _success(request, model, attachment_model, fk_name):
    """"File has been succesfully uploaded to a FOIA/composer"""
    try:
        foia = model.objects.get(pk=request.POST.get("id"))
    except model.DoesNotExist:
        return HttpResponseBadRequest()
    if not foia.has_perm(request.user, "upload_attachment"):
        return HttpResponseForbidden()
    if "key" not in request.POST:
        return HttpResponseBadRequest()
    if len(request.POST["key"]) > 255:
        return HttpResponseBadRequest()

    attachment = attachment_model(
        user=request.user, date_time_stamp=timezone.now(), **{fk_name: foia}
    )
    attachment.ffile.name = request.POST["key"]
    attachment.save()

    return HttpResponse()


@login_or_agency_required
def success_request(request):
    """"File has been succesfully uploaded to a FOIA"""
    return _success(request, FOIARequest, OutboundRequestAttachment, "foia")


@login_required
def success_composer(request):
    """"File has been succesfully uploaded to a composer"""
    return _success(request, FOIAComposer, OutboundComposerAttachment, "composer")


@login_required
def success_comm(request):
    """"File has been succesfully uploaded directly to a communication"""
    try:
        comm = FOIACommunication.objects.get(pk=request.POST.get("id"))
    except FOIACommunication.DoesNotExist:
        return HttpResponseBadRequest()
    if not (comm.foia and comm.foia.has_perm(request.user, "upload_attachment")):
        return HttpResponseForbidden()
    if "key" not in request.POST:
        return HttpResponseBadRequest()
    if len(request.POST["key"]) > 255:
        return HttpResponseBadRequest()

    comm.attach_file(
        path=request.POST["key"],
        name=os.path.basename(request.POST["key"]),
        source=request.user.profile.full_name,
    )

    return HttpResponse()


def _session(request, model):
    """"Get the initial file list"""
    try:
        foia = model.objects.get(pk=request.GET.get("id"))
    except model.DoesNotExist:
        return HttpResponseBadRequest()
    if not foia.has_perm(request.user, "upload_attachment"):
        return HttpResponseForbidden()

    attms = foia.pending_attachments.filter(user=request.user, sent=False)

    data = []
    for attm in attms:
        data.append(
            {
                "name": attm.name(),
                "uuid": attm.pk,
                "size": attm.ffile.size,
                "s3Key": attm.ffile.name,
            }
        )
    return JsonResponse(data, safe=False)


@login_or_agency_required
def session_request(request):
    """Get the initial file list for a request"""
    return _session(request, FOIARequest)


@login_required
def session_composer(request):
    """Get the initial file list for a composer"""
    return _session(request, FOIAComposer)


def _delete(request, model):
    """Delete a pending attachment"""
    try:
        attm = model.objects.get(ffile=request.POST.get("key"), sent=False)
    except model.DoesNotExist:
        return HttpResponseBadRequest()

    if request.user.is_authenticated:
        user = request.user
    elif model is OutboundRequestAttachment and request.session.get(
        f"foiapasscode:{attm.foia_id}"
    ):
        user = attm.foia.agency.get_user()

    if attm.user != user:
        return HttpResponseForbidden()

    if not attm.attached_to.has_perm(user, "upload_attachment"):
        return HttpResponseForbidden()

    attm.delete()
    return HttpResponse()


def delete_request(request):
    """Delete a pending attachment from a FOIA Request"""
    return _delete(request, OutboundRequestAttachment)


@login_required
def delete_composer(request):
    """Delete a pending attachment from a FOIA Composer"""
    return _delete(request, OutboundComposerAttachment)


def sign(request):
    """Sign the data to upload to S3"""
    payload = json.loads(request.body)
    if "headers" in payload:
        return JsonResponse(_sign_headers(payload["headers"]))
    elif _is_valid_policy(request.user, payload):
        return JsonResponse(_sign_policy_document(payload))
    else:
        return JsonResponse({"invalid": True}, status=400)


def _is_valid_policy(user, policy_document):
    """
    Verify the policy document has not been tampered with client-side
    before sending it off.
    """
    bucket = None
    parsed_max_size = None

    if user.has_perm("foia.unlimited_attachment_size"):
        max_size = None
    else:
        max_size = settings.MAX_ATTACHMENT_SIZE

    for condition in policy_document["conditions"]:
        if isinstance(condition, list) and condition[0] == "content-length-range":
            parsed_max_size = int(condition[2])
        elif "bucket" in condition:
            bucket = condition["bucket"]

    return bucket == settings.AWS_STORAGE_BUCKET_NAME and parsed_max_size == max_size


def _sign_policy_document(policy_document):
    """Sign and return the policy doucument for a simple upload.
    http://aws.amazon.com/articles/1434/#signyours3postform"""
    policy = base64.b64encode(json.dumps(policy_document).encode("utf8"))
    signature = base64.b64encode(
        hmac.new(
            settings.AWS_SECRET_ACCESS_KEY.encode("utf8"), policy, hashlib.sha1
        ).digest()
    )
    return {"policy": policy.decode("utf8"), "signature": signature.decode("utf8")}


def _sign_headers(headers):
    """Sign and return the headers for a chunked upload"""
    return {
        "signature": base64.b64encode(
            hmac.new(
                settings.AWS_SECRET_ACCESS_KEY.encode("utf8"),
                headers.encode("utf8"),
                hashlib.sha1,
            ).digest()
        ).decode("utf8")
    }


def _key_name_trim(name):
    """
    Total name cannot be longer than 255, but we limit the base name to 100
    to give room for the directory and because that's plenty long
    """
    max_len = 100
    if len(name) > max_len:
        base, ext = os.path.splitext(name)
        if len(ext) > max_len:
            # if someone give us a large extension just cut part of it off
            name = name[:max_len]
        else:
            # otherwise truncate the base and put the extension back on
            name = base[: max_len - len(ext)] + ext
    return name


def _key_name(request, model, id_name):
    """Generate the S3 key name from the filename"""
    name = request.POST.get("name")
    attached_id = request.POST.get("id")
    name = _key_name_trim(name)
    attachment = model(user=request.user, **{id_name: attached_id})
    key = attachment.ffile.field.generate_filename(attachment.ffile.instance, name)
    key = default_storage.get_available_name(key)
    return JsonResponse({"key": key})


@login_or_agency_required
def key_name_request(request):
    """Generate the S3 key name for a FOIA Request"""
    return _key_name(request, OutboundRequestAttachment, "foia_id")


@login_required
def key_name_composer(request):
    """Generate the S3 key name for a FOIA Composer"""
    return _key_name(request, OutboundComposerAttachment, "composer_id")


@login_required
def key_name_comm(request):
    """Generate the S3 key name from the filename"""
    name = request.POST.get("name")
    name = _key_name_trim(name)
    file_ = FOIAFile()
    key = file_.ffile.field.generate_filename(file_.ffile.instance, name)
    key = default_storage.get_available_name(key)
    return JsonResponse({"key": key})


@login_required
def blank(request):
    """Workaround for IE9 and older"""
    # pylint: disable=unused-argument
    return HttpResponse()
