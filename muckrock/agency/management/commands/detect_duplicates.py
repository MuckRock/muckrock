# Django
from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import reverse

# Standard Library
import csv

# Third Party
from fuzzywuzzy import fuzz, process
from smart_open.smart_open_lib import smart_open

# MuckRock
from muckrock.agency.models import Agency
from muckrock.jurisdiction.models import Jurisdiction


class Command(BaseCommand):
    """Detect duplicate agencies"""

    def add_arguments(self, parser):
        parser.add_argument("--cutoff", type=int, default=83)

    def handle(self, *args, **kwargs):
        cutoff = kwargs["cutoff"]
        with smart_open(
            f"s3://{settings.AWS_STORAGE_BUCKET_NAME}/agency_duplicates.csv", "w"
        ) as file:
            writer = csv.writer(file)
            writer.writerow(
                [
                    "jurisdiction id",
                    "jurisdiction name",
                    "agency id",
                    "agency name",
                    "agency url",
                    "agency admin",
                    "match id",
                    "match name",
                    "match url",
                    "match admin",
                    "match score",
                ]
            )
            print("Starting agency duplicate detection...")
            jurisdictions = Jurisdiction.objects.exclude(agencies=None)
            print(f"There are {jurisdictions.count()} total jurisdictions")
            for i, jurisdiction in enumerate(
                jurisdictions.select_related("parent").iterator()
            ):
                agencies = Agency.objects.filter(
                    status="approved", jurisdiction=jurisdiction
                ).select_related("jurisdiction")
                print(f"{i} - {jurisdiction} - agencies: {agencies.count()}")
                for agency in agencies:
                    matches = process.extractBests(
                        agency.name,
                        {a: a.name for a in agencies if a.pk > agency.pk},
                        scorer=fuzz.partial_ratio,
                        score_cutoff=cutoff,
                    )
                    for _name, score, match in matches:
                        writer.writerow(
                            [
                                jurisdiction.pk,
                                str(jurisdiction),
                                agency.pk,
                                str(agency),
                                settings.MUCKROCK_URL + agency.get_absolute_url(),
                                settings.MUCKROCK_URL
                                + reverse(
                                    "admin:agency_agency_change", args=(agency.pk,)
                                ),
                                match.pk,
                                str(match),
                                settings.MUCKROCK_URL + match.get_absolute_url(),
                                settings.MUCKROCK_URL
                                + reverse(
                                    "admin:agency_agency_change", args=(match.pk,)
                                ),
                                score,
                            ]
                        )
