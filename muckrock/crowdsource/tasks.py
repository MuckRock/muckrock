"""
Celery tasks for the crowdsource application
"""

# Django
from celery.task import task
from django.conf import settings

# Standard Library
import logging
from urllib import quote_plus

# Third Party
import requests

# MuckRock
from muckrock.crowdsource.models import Crowdsource

logger = logging.getLogger(__name__)


@task(name='muckrock.crowdsource.tasks.datum_per_page')
def datum_per_page(crowdsource_pk, doc_id, metadata, **kwargs):
    """Create a crowdsource data item for each page of the document"""

    crowdsource = Crowdsource.objects.get(pk=crowdsource_pk)

    doc_id = quote_plus(doc_id.encode('utf-8'))
    resp = requests.get(
        u'https://www.documentcloud.org'
        u'/api/documents/{}.json'.format(
            doc_id,
        )
    )
    try:
        resp_json = resp.json()
    except ValueError as exc:
        datum_per_page.retry(
            args=[crowdsource_pk, doc_id, metadata],
            countdown=300,
            kwargs=kwargs,
            exc=exc,
        )
    pages = resp_json['document']['pages']
    for i in xrange(1, pages + 1):
        url = (
            u'https://www.documentcloud.org/documents/'
            u'{}/pages/{}.html'.format(doc_id, i)
        )
        crowdsource.data.create(
            url=url,
            metadata=metadata,
        )


@task(name='muckrock.crowdsource.tasks.import_doccloud_proj')
def import_doccloud_proj(
    crowdsource_pk, proj_id, metadata, doccloud_each_page, **kwargs
):
    """Import documents from a document cloud project"""

    crowdsource = Crowdsource.objects.get(pk=crowdsource_pk)
    json_url = (
        'https://www.documentcloud.org/api/projects/{}.json'.format(proj_id)
    )

    resp = requests.get(
        json_url,
        auth=(settings.DOCUMENTCLOUD_USERNAME, settings.DOCUMENTCLOUD_PASSWORD),
    )
    try:
        resp_json = resp.json()
    except ValueError as exc:
        import_doccloud_proj.retry(
            args=[crowdsource_pk, proj_id, metadata],
            countdown=300,
            kwargs=kwargs,
            exc=exc,
        )
    else:
        if 'error' in resp_json:
            logger.warn('Error importing DocCloud project: %s', proj_id)
            return
        for doc_id in resp_json['project']['document_ids']:
            if doccloud_each_page:
                datum_per_page.delay(
                    crowdsource.pk,
                    doc_id,
                    metadata,
                )
            else:
                crowdsource.data.create(
                    url='https://www.documentcloud.org/documents/{}.html'
                    .format(doc_id),
                    metadata=metadata,
                )
