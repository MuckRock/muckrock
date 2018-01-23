"""
Celery tasks for the crowdsource application
"""

from celery.task import task

import requests
from urllib import quote_plus

from muckrock.crowdsource.models import Crowdsource

@task(name='muckrock.crowdsource.tasks.datum_per_page')
def datum_per_page(crowdsource_pk, doc_id, metadata, **kwargs):
    """Create a crowdsource data item for each page of the document"""

    crowdsource = Crowdsource.objects.get(pk=crowdsource_pk)

    doc_id = quote_plus(doc_id.encode('utf-8'))
    resp = requests.get(
            u'https://www.documentcloud.org'
            u'/api/documents/{}.json'.format(
                doc_id,
                ))
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
