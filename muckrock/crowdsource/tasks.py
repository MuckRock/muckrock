"""
Celery tasks for the crowdsource application
"""

# Django
from celery.task import task
from django.conf import settings

# Standard Library
import logging
from urllib.parse import quote_plus

# Third Party
import requests
import unicodecsv as csv

# MuckRock
from muckrock.core.tasks import AsyncFileDownloadTask
from muckrock.crowdsource.models import Crowdsource

logger = logging.getLogger(__name__)


@task(name='muckrock.crowdsource.tasks.datum_per_page')
def datum_per_page(crowdsource_pk, doc_id, metadata, **kwargs):
    """Create a crowdsource data item for each page of the document"""

    crowdsource = Crowdsource.objects.get(pk=crowdsource_pk)

    doc_id = quote_plus(doc_id.encode('utf-8'))
    resp = requests.get(
        'https://www.documentcloud.org'
        '/api/documents/{}.json'.format(
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
    for i in range(1, pages + 1):
        url = (
            'https://www.documentcloud.org/documents/'
            '{}/pages/{}.html'.format(doc_id, i)
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


class ExportCsv(AsyncFileDownloadTask):
    """Export the results of the crowdsource for the user"""
    dir_name = 'exported_csv'
    file_name = 'results.csv'
    text_template = 'message/notification/csv_export.txt'
    html_template = 'message/notification/csv_export.html'
    subject = 'Your CSV Export'

    def __init__(self, user_pk, crowdsource_pk):
        super(ExportCsv, self).__init__(user_pk, crowdsource_pk)
        self.crowdsource = Crowdsource.objects.get(pk=crowdsource_pk)

    def generate_file(self, out_file):
        """Export all responses as a CSV file"""
        metadata_keys = self.crowdsource.get_metadata_keys()
        include_emails = self.user.is_staff

        writer = csv.writer(out_file)
        writer.writerow(
            self.crowdsource.get_header_values(metadata_keys, include_emails)
        )
        for csr in self.crowdsource.responses.all().iterator():
            writer.writerow(csr.get_values(metadata_keys, include_emails))


@task(time_limit=1800, name='muckrock.crowdsource.tasks.export_csv')
def export_csv(crowdsource_pk, user_pk):
    """Export the results of the crowdsource for the user"""
    ExportCsv(user_pk, crowdsource_pk).run()
