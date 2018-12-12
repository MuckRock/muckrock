"""Views for the squarelet app"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# Django
from django.conf import settings
from django.http.response import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt

# Standard Library
import hashlib
import hmac
import time

# MuckRock
from muckrock.squarelet.tasks import pull_data


@csrf_exempt
def cache_invalidate(request):
    """Receive a cache invalidation from squarelet"""

    type_ = request.POST.get('type', '')
    uuid = request.POST.get('uuid', '')
    timestamp = request.POST.get('timestamp', '')
    signature = request.POST.get('signature', '')

    # verify signature
    hmac_digest = hmac.new(
        key=settings.SQUARELET_SECRET_KEY,
        msg='{}{}{}'.format(timestamp, type_, uuid),
        digestmod=hashlib.sha256,
    ).hexdigest()
    match = hmac.compare_digest(
        unicode(signature),
        unicode(hmac_digest),
    )
    timestamp_current = int(timestamp) + 300 > time.time()
    if not match or not timestamp_current:
        return HttpResponseForbidden()

    # pull the new data asynchrnously
    pull_data.delay(type_, uuid)
    return HttpResponse('OK')
