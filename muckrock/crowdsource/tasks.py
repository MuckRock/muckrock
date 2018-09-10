"""
Celery tasks for the crowdsource application
"""

# Django
from celery.task import task
from django.conf import settings
from django.contrib.auth.models import User

# Standard Library
import logging
from datetime import date
from hashlib import md5
from time import time
from urllib import quote_plus

# Third Party
import requests
import unicodecsv as csv
from boto.s3.connection import S3Connection
from smart_open.smart_open_lib import smart_open

# MuckRock
from muckrock.crowdsource.models import Crowdsource
from muckrock.message.email import TemplateEmail

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
        resp.raise_for_status()
        resp_json = resp.json()
    except (ValueError, requests.exceptions.HTTPError) as exc:
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


@task(time_limit=1800, name='muckrock.crowdsource.tasks.export_csv')
def export_csv(crowdsource_pk, user_pk):
    """Export the results of the crowdsource for the user"""
    crowdsource = Crowdsource.objects.get(pk=crowdsource_pk)
    metadata_keys = crowdsource.get_metadata_keys()
    user = User.objects.get(pk=user_pk)
    include_emails = user.is_staff

    conn = S3Connection(
        settings.AWS_ACCESS_KEY_ID,
        settings.AWS_SECRET_ACCESS_KEY,
    )
    bucket = conn.get_bucket(settings.AWS_STORAGE_BUCKET_NAME)
    today = date.today()
    file_key = 'exported_csv/{y:4d}/{m:02d}/{d:02d}/{md5}/results.csv'.format(
        y=today.year,
        m=today.month,
        d=today.day,
        md5=md5(
            '{}{}{}'.format(
                int(time()),
                crowdsource_pk,
                settings.SECRET_KEY,
            )
        ).hexdigest(),
    )
    key = bucket.new_key(file_key)
    with smart_open(key, 'wb') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(
            crowdsource.get_header_values(metadata_keys, include_emails)
        )
        for csr in crowdsource.responses.all().iterator():
            writer.writerow(csr.get_values(metadata_keys, include_emails))
    key.set_acl('public-read')

    notification = TemplateEmail(
        user=user,
        extra_context={'file': file_key},
        text_template='message/notification/csv_export.txt',
        html_template='message/notification/csv_export.html',
        subject='Your CSV Export',
    )
    notification.send(fail_silently=False)
