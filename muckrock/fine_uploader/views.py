"""Views to interact with Fine Uploader AJAX calls"""

# Django
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    JsonResponse,
)
from django.utils import timezone

# Standard Library
import os
from functools import wraps

# Third Party
import boto3

# MuckRock
from muckrock.core.storage import MediaRootS3BotoStorage
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

    # Send the client the ID to update its reference
    return JsonResponse({"id": attachment.id})


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

    attachment = comm.attach_file(
        path=request.POST["key"],
        name=os.path.basename(request.POST["key"]),
        source=request.user.profile.full_name,
    )

    return JsonResponse({"id": attachment.id})


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
                "s3Bucket": settings.AWS_MEDIA_BUCKET_NAME,
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


def _delete(request, model, idx):
    """Delete a pending attachment"""
    try:
        attm = model.objects.get(pk=idx, sent=False)
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


def delete_request(request, idx):
    """Delete a pending attachment from a FOIA Request"""
    return _delete(request, OutboundRequestAttachment, idx)


@login_required
def delete_composer(request, idx):
    """Delete a pending attachment from a FOIA Composer"""
    return _delete(request, OutboundComposerAttachment, idx)


def _build_presigned_url(key, contentType, user=None):
    """Generate a policy document and presigned URL for an upload
    https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-presigned-urls.html#generating-a-presigned-url-to-upload-a-file"""

    # Validate MIME type
    if not contentType in settings.ALLOWED_FILE_MIMES:
        raise ValidationError("Invalid file type")

    bucket = settings.AWS_MEDIA_BUCKET_NAME
    conditions = [
        # Restrict uploads to specific bucket/key/ACL
        {"acl": settings.AWS_DEFAULT_ACL},
        {"bucket": bucket},
        {"key": key},
        {"success_action_status": "200"},
        {"Content-Type": contentType},
        # Whitelist metadata headers
        ["starts-with", "$x-amz-meta-qqfilename", ""],
        ["starts-with", "$x-amz-meta-qquuid", ""],
        ["starts-with", "$x-amz-meta-qqtotalfilesize", ""],
    ]

    if not user or not user.has_perm("foia.unlimited_attachment_size"):
        conditions.append(["content-length-range", "0", settings.MAX_ATTACHMENT_SIZE])

    s3 = boto3.client("s3")
    url_data = s3.generate_presigned_post(
        bucket, key, Conditions=conditions, ExpiresIn=60
    )

    url_data["fields"]["acl"] = settings.AWS_DEFAULT_ACL
    url_data["fields"]["success_action_status"] = 200
    url_data["fields"]["Content-Type"] = contentType

    return url_data


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


def _get_key(request, model, id_name=None):
    """Generate the S3 key name from the filename, while guaranteeing uniqueness"""
    name = request.POST.get("name")
    attached_id = request.POST.get("id")
    name = _key_name_trim(name)
    attachment = (
        model(user=request.user, **{id_name: attached_id}) if id_name else model()
    )
    key = attachment.ffile.field.generate_filename(attachment.ffile.instance, name)
    return default_storage.get_available_name(key)


def _preupload(request, model, id_name=None):
    """Generates request info so the client can update directly to S3"""
    key = _get_key(request, model, id_name)
    contentType = request.POST.get("type")

    try:
        presigned_url = _build_presigned_url(key, contentType, user=request.user)
    except ValidationError as e:
        return JsonResponse({"error": e.message}, status=400)

    return JsonResponse(presigned_url)


@login_or_agency_required
def preupload_request(request):
    """Generate upload info for a FOIA Request"""
    return _preupload(request, OutboundRequestAttachment, "foia_id")


@login_required
def preupload_composer(request):
    """Generate upload info for a FOIA Composer"""
    return _preupload(request, OutboundComposerAttachment, "composer_id")


@login_required
def preupload_comm(request):
    """Generate upload info for a communication"""
    return _preupload(request, FOIAFile)


@login_required
def blank(request):
    """Workaround for IE9 and older"""
    # pylint: disable=unused-argument
    return HttpResponse()
