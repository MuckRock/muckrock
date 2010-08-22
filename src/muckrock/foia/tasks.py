"""Celery Tasks for the FOIA application"""

from celery.decorators import periodic_task, task
from celery.task.schedules import crontab
from django.core import management
from settings import DOCUMNETCLOUD_USERNAME, DOCUMENTCLOUD_PASSWORD

import base64
import json
import urllib2
from vendor import MultipartPostHandler

from foia.models import FOIADocument


@task(ignore_result=True)
def upload_document_cloud(doc_pk, change, **kwargs):
    """Upload a document to Document Cloud"""

    try:
        doc = FOIADocument.objects.get(pk=doc_pk)
    except FOIADocument.DoesNotExist, exc:
        # pylint: disable-msg=E1101
        # give database time to sync
        upload_document_cloud.retry(args=[doc.pk, change], kwargs=kwargs, exc=exc)

    if doc.doc_id and not change:
        # not change means we are uploading a new one - it should not have an id yet
        return

    # coerced from unicode to regular strings in order to avoid encoding errors
    params = {
        'title': str(doc.title),
        'source': str(doc.source),
        'description': str(doc.description),
        'access': str(doc.access),
        'related_article': str('http://www.muckrock.com' + doc.foia.get_absolute_url()),
        }
    if change:
        params['_method'] = str('put')
        url = '/documents/%s.json' % doc.doc_id
    else:
        params['file'] = open(str(doc.document.path), 'rb')
        url = '/upload.json'

    opener = urllib2.build_opener(MultipartPostHandler.MultipartPostHandler)
    request = urllib2.Request('https://www.documentcloud.org/api/%s' % url, params)
    # This is just standard username/password encoding
    auth = base64.encodestring('%s:%s' % (DOCUMNETCLOUD_USERNAME, DOCUMENTCLOUD_PASSWORD))[:-1]
    request.add_header('Authorization', 'Basic %s' % auth)

    try:
        ret = opener.open(request).read()
        if not change:
            info = json.loads(ret)
            doc.doc_id = info['id']
            doc.save()
    except urllib2.URLError, exc:
        # pylint: disable-msg=E1101
        upload_document_cloud.retry(args=[doc.pk, change], kwargs=kwargs, exc=exc)


@periodic_task(run_every=crontab(hour='1', minute='0', day_of_week='*'))
def update_index():
    """Update the search index every day at 1AM"""
    management.call_command('update_index')
