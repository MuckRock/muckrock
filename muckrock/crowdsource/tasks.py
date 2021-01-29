"""
Celery tasks for the crowdsource application
"""

# Django
from celery.task import task
from django.conf import settings

# Standard Library
import csv
import logging
from urllib.parse import quote_plus

# Third Party
import requests
from documentcloud import DocumentCloud
from documentcloud.exceptions import DocumentCloudError

# MuckRock
from muckrock.core.tasks import AsyncFileDownloadTask
from muckrock.crowdsource.models import Crowdsource

logger = logging.getLogger(__name__)


@task(
    name="muckrock.crowdsource.tasks.datum_per_page",
    autoretry_for=(DocumentCloudError,),
    retry_backoff=60,
    retry_kwargs={"max_retries": 3},
)
def datum_per_page(crowdsource_pk, doc_id, metadata):
    """Create a crowdsource data item for each page of the document"""

    crowdsource = Crowdsource.objects.get(pk=crowdsource_pk)
    dc_client = DocumentCloud(
        username=settings.DOCUMENTCLOUD_BETA_USERNAME,
        password=settings.DOCUMENTCLOUD_BETA_PASSWORD,
        base_uri=f"{settings.DOCCLOUD_API_URL}/api/",
        auth_uri=f"{settings.SQUARELET_URL}/api/",
    )
    document = dc_client.documents.get(doc_id)
    for i in range(1, document.pages + 1):
        crowdsource.data.create(
            url=f"{document.canonical_url}/pages/{i}", metadata=metadata
        )


@task(
    name="muckrock.crowdsource.tasks.import_doccloud_proj",
    autoretry_for=(DocumentCloudError,),
    retry_backoff=60,
    retry_kwargs={"max_retries": 3},
)
def import_doccloud_proj(crowdsource_pk, proj_id, metadata, doccloud_each_page):
    """Import documents from a document cloud project"""
    crowdsource = Crowdsource.objects.get(pk=crowdsource_pk)

    dc_client = DocumentCloud(
        username=settings.DOCUMENTCLOUD_BETA_USERNAME,
        password=settings.DOCUMENTCLOUD_BETA_PASSWORD,
        base_uri=f"{settings.DOCCLOUD_API_URL}/api/",
        auth_uri=f"{settings.SQUARELET_URL}/api/",
    )
    project = dc_client.projects.get(proj_id)

    for document in project.documents:
        if doccloud_each_page:
            datum_per_page.delay(crowdsource.pk, document.id, metadata)
        else:
            crowdsource.data.create(url=document.canonical_url, metadata=metadata)


class ExportCsv(AsyncFileDownloadTask):
    """Export the results of the crowdsource for the user"""

    dir_name = "exported_csv"
    file_name = "results.csv"
    text_template = "message/notification/csv_export.txt"
    html_template = "message/notification/csv_export.html"
    subject = "Your CSV Export"

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


@task(time_limit=1800, name="muckrock.crowdsource.tasks.export_csv")
def export_csv(crowdsource_pk, user_pk):
    """Export the results of the crowdsource for the user"""
    ExportCsv(user_pk, crowdsource_pk).run()
