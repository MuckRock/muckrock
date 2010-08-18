"""Celery Tasks for the FOIA application"""

from settings import DOCUMNETCLOUD_USERNAME, DOCUMENTCLOUD_PASSWORD

from foia.models import FOIADocument

import base64
import json
import urllib2
from vendor import MultipartPostHandler
from celery.decorators import task

@task(ignore_result=True)
def upload_document_cloud(doc_pk, **kwargs):
    """Upload a document to Document Cloud"""

    doc = FOIADocument.objects.get(pk=doc_pk)

    if doc.doc_id:
        # already been uploaded
        return

    # coerced from unicode to regular strings in order to avoid encoding errors
    params = {
        'file': open(str(doc.document.path), 'rb'),
        'title': str(doc.title),
        'source': str(doc.source),
        'description': str(doc.description),
        'access': str(doc.access),
        }

    opener = urllib2.build_opener(MultipartPostHandler.MultipartPostHandler)
    request = urllib2.Request('https://www.documentcloud.org/api/upload.json', params)
    # This is just standard username/password encoding
    auth = base64.encodestring('%s:%s' % (DOCUMNETCLOUD_USERNAME, DOCUMENTCLOUD_PASSWORD))[:-1]
    request.add_header('Authorization', 'Basic %s' % auth)

    try:
        ret = opener.open(request).read()
        info =  json.loads(ret)
        doc.doc_id = info['id']
        doc.save()
    except urllib2.URLError, exc:
        # pylint: disable-msg=E1101
        upload_document_cloud.retry(args=[doc.pk], kwargs=kwargs, exc=exc)
