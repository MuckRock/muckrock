"""Celery Tasks for the agency application"""

# Django
from celery.schedules import crontab
from celery.task import periodic_task, task

# Standard Library
import csv
import os

# Third Party
from raven import Client
from raven.contrib.celery import register_logger_signal, register_signal
from smart_open.smart_open_lib import smart_open

# MuckRock
from muckrock.agency.importer import CSVReader, Importer
from muckrock.core.tasks import AsyncFileDownloadTask
from muckrock.foia.models import FOIARequest
from muckrock.task.models import ReviewAgencyTask

client = Client(os.environ.get("SENTRY_DSN"))
register_logger_signal(client)
register_signal(client)


@periodic_task(
    run_every=crontab(day_of_week="sunday", hour=4, minute=0),
    name="muckrock.agency.tasks.stale",
)
def stale():
    """Record all stale agencies once a week"""
    for foia in FOIARequest.objects.get_stale():
        ReviewAgencyTask.objects.ensure_one_created(
            agency=foia.agency, resolved=False, source="stale"
        )


class MassImport(AsyncFileDownloadTask):
    """Do a mass import of agency data"""

    dir_name = "agency_mass_import"
    file_name = "agencies.csv"
    text_template = "message/notification/agency_mass_import.txt"
    html_template = "message/notification/agency_mass_import.html"
    subject = "Agency Mass Import Complete"
    match_fields = [
        "agency",
        "agency_status",
        "jurisdiction",
        "jurisdiction_status",
        "match_agency_url",
        "match_agency_id",
        "match_agency_name",
        "match_agency_score",
    ]
    import_fields = match_fields + [
        "email",
        "cc_emails",
        "email_status",
        "phone",
        "phone_status",
        "fax",
        "fax_status",
        "address_suite",
        "address_street",
        "address_city",
        "address_state",
        "address_zip",
        "address_status",
        "portal_type",
        "portal_url",
        "portal_status",
        "aliases",
        "aliases_status",
        "foia_website",
        "foia_website_status",
        "website",
        "website_status",
        "requires_proxy",
        "requires_proxy_status",
    ]

    def __init__(self, user_pk, file_path, match, dry):
        super(MassImport, self).__init__(user_pk, file_path)
        self.file_path = file_path
        self.match = match
        self.dry = dry

    def generate_file(self, out_file):
        """Do the import and generate the CSV file as output"""
        writer = csv.writer(out_file)
        with smart_open(self.file_path, "r") as in_file:
            reader = CSVReader(in_file)
            importer = Importer(reader)

            if self.match:
                data = importer.match()
                fields = self.match_fields
            else:
                data = importer.import_(dry=self.dry)
                fields = self.import_fields

            writer.writerow(fields)
            for datum in data:
                writer.writerow(datum.get(f, "") for f in fields)


@task(ignore_result=True, time_limit=1800, name="muckrock.agency.tasks.mass_import")
def mass_import(user_pk, file_path, match, dry):
    """Mass import a CSV of agencies"""
    MassImport(user_pk, file_path, match, dry).run()
