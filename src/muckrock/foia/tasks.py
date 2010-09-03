"""Celery Tasks for the FOIA application"""

from celery.decorators import periodic_task, task
from celery.task.schedules import crontab
from django.core import management
from settings import DOCUMNETCLOUD_USERNAME, DOCUMENTCLOUD_PASSWORD, \
                     GA_USERNAME, GA_PASSWORD, GA_ID

import base64
import gdata.analytics.service
import json
import re
import sys
import urllib2
from datetime import date, timedelta
from vendor import MultipartPostHandler

from foia.models import FOIADocument, FOIADocTopViewed


@task(ignore_result=True)
def upload_document_cloud(doc_pk, change, **kwargs):
    """Upload a document to Document Cloud"""

    try:
        doc = FOIADocument.objects.get(pk=doc_pk)
    except FOIADocument.DoesNotExist, exc:
        # pylint: disable-msg=E1101
        # give database time to sync
        upload_document_cloud.retry(args=[doc_pk, change], kwargs=kwargs, exc=exc)

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
        # pylint: disable-msg=E1101
            info = json.loads(ret)
            doc.doc_id = info['id']
            doc.save()
            set_document_cloud_pages.apply_async(args=[doc.pk], countdown=300)
    except urllib2.URLError, exc:
        # pylint: disable-msg=E1101
        upload_document_cloud.retry(args=[doc.pk, change], kwargs=kwargs, exc=exc)


@task(ignore_result=True)
def set_document_cloud_pages(doc_pk, **kwargs):
    """Get the number of pages from the document cloud server and save it locally"""

    doc = FOIADocument.objects.get(pk=doc_pk)

    if doc.pages:
        # already has pages set, just return
        return

    request = urllib2.Request('https://www.documentcloud.org/api/documents/%s.json' % doc.doc_id)
    # This is just standard username/password encoding
    auth = base64.encodestring('%s:%s' % (DOCUMNETCLOUD_USERNAME, DOCUMENTCLOUD_PASSWORD))[:-1]
    request.add_header('Authorization', 'Basic %s' % auth)

    try:
        ret = urllib2.urlopen(request).read()
        info = json.loads(ret)
        doc.pages = info['document']['pages']
        doc.save()
    except urllib2.URLError, exc:
        # pylint: disable-msg=E1101
        set_document_cloud_pages.retry(args=[doc.pk], countdown=300, kwargs=kwargs, exc=exc)


@periodic_task(run_every=crontab(hour=1, minute=10))
def set_top_viewed_docs():
    """Get the top 5 most viewed documents from Google Analytics and save them locally"""

    client = gdata.analytics.service.AnalyticsDataService()
    client.ClientLogin(GA_USERNAME, GA_PASSWORD)
    data = client.GetData(ids=GA_ID, dimensions='ga:pagePath', metrics='ga:pageviews',
                          start_date=(date.today() - timedelta(days=30)).isoformat(),
                          end_date=date.today().isoformat(), sort='-ga:pageviews')
    top_doc_paths = [entry.title.text for entry in data.entry
                if entry.title.text.startswith('ga:pagePath=/foi/doc_cloud/')]
    path_re = re.compile('ga:pagePath=/foi/doc_cloud/(?P<doc_id>[a-z0-9-]+)/')
    top_docs =[]
    try:
        for doc_path in top_doc_paths:
            if len(top_docs) >= 5:
                break
            try:
                top_docs.append(FOIADocument.objects.get(
                    doc_id=path_re.match(doc_path).group('doc_id')))
            except FOIADocument.DoesNotExist:
                pass
    except AttributeError:
        print >> sys.stderr, 'Error in set_top_viewed_docs'
        print >> sys.stderr, top_docs
        return

    for i, doc in enumerate(top_docs):
        tv_doc = FOIADocTopViewed.objects.get_or_create(rank=i+1, defaults={'doc': doc})
        tv_doc.doc = doc
        tv_doc.save()


@periodic_task(run_every=crontab(hour=1, minute=0))
def update_index():
    """Update the search index every day at 1AM"""
    management.call_command('update_index')
