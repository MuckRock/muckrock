"""
Celery tasks for the crowdsource application
"""

# Django
from celery.task import task

# Standard Library
import re
from urllib import quote_plus

# Third Party
import requests

# MuckRock
from muckrock.crowdsource.models import Crowdsource

DOCUMENT_URL_RE = re.compile(
    r'https?://www[.]documentcloud[.]org/documents/'
    r'(?P<doc_id>[0-9A-Za-z-]+)[.]html'
)


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
    crowdsource_pk, url, metadata, doccloud_each_page, **kwargs
):
    """Import documents from a document cloud project"""

    crowdsource = Crowdsource.objects.get(pk=crowdsource_pk)
    json_url = url[:-4] + 'json'

    resp = requests.get(json_url)
    try:
        resp_json = resp.json()
    except ValueError as exc:
        import_doccloud_proj.retry(
            args=[crowdsource_pk, url, metadata],
            countdown=300,
            kwargs=kwargs,
            exc=exc,
        )
    else:
        for document in resp_json['documents']:
            doc_match = DOCUMENT_URL_RE.match(url)
            if doccloud_each_page and doc_match:
                datum_per_page.delay(
                    crowdsource.pk,
                    doc_match.group('doc_id'),
                    metadata,
                )
            else:
                crowdsource.data.create(
                    url=document,
                    metadata=metadata,
                )
