"""
Custom importers for school agencies
"""

# Django
from django.conf import settings
from django.template.defaultfilters import slugify

# Standard Library
import csv

# Third Party
from smart_open.smart_open_lib import smart_open

# MuckRock
from muckrock.agency.models import (
    Agency,
    AgencyAddress,
    AgencyEmail,
    AgencyPhone,
    AgencyType,
)
from muckrock.communication.models import Address, EmailAddress, PhoneNumber
from muckrock.jurisdiction.models import Jurisdiction

# columns
CD_CODE = 0
COUNTY = 1
DISTRICT = 2
STREET = 3
CITY = 4
ZIP = 5
STATE = 6
MAIL_STREET = 7
MAIL_CITY = 8
MAIL_ZIP = 9
MAIL_STATE = 10
PHONE = 11
EXT = 12
FIRST_NAME = 13
LAST_NAME = 14
EMAIL = 15
LATITUDE = 16
LONGITUDE = 17
DOC = 18
DOC_TYPE = 19
STATUS = 20
LAST_UPDATE = 21


def import_schools(file_name):
    """Import schools from spreadsheet"""
    # pylint: disable=too-many-locals
    s3_path = f"s3://{settings.AWS_MEDIA_BUCKET_NAME}/{file_name}"
    school_district = AgencyType.objects.get(name="School District")
    with smart_open(s3_path) as tmp_file:
        reader = csv.reader(tmp_file)
        for row in reader:
            print("~~~")
            print(row[DISTRICT])
            try:
                parent = Jurisdiction.objects.get(abbrev=row[STATE])
                county = Jurisdiction.objects.get(
                    name="%s County" % row[COUNTY], parent=parent, level="l"
                )
            except (
                Jurisdiction.DoesNotExist,
                Jurisdiction.MultipleObjectsReturned,
            ) as exc:
                print("****")
                print("Jurisdiction error")
                print(row)
                print(exc)
                print("****")
            else:
                agency, created = Agency.objects.get_or_create(
                    name=row[DISTRICT],
                    slug=slugify(row[DISTRICT]),
                    jurisdiction=county,
                    status="approved",
                    defaults=dict(
                        contact_first_name=row[FIRST_NAME],
                        contact_last_name=row[LAST_NAME],
                    ),
                )
                if not created:
                    print("agency already existed")
                print(agency.pk)
                agency.types.add(school_district)
                address, _ = Address.objects.get_or_create(
                    address="{name}\n{street}\n{city}, {state} {zip}".format(
                        name=row[DISTRICT],
                        street=row[MAIL_STREET],
                        city=row[MAIL_CITY],
                        state=row[MAIL_STATE],
                        zip=row[MAIL_ZIP],
                    )
                )
                AgencyAddress.objects.get_or_create(
                    agency=agency, address=address, request_type="primary"
                )
                number = row[PHONE]
                if number:
                    if row[EXT]:
                        number += " x%s" % row[EXT]
                    phone, _ = PhoneNumber.objects.get_or_create(
                        number=number, type="phone"
                    )
                    AgencyPhone.objects.get_or_create(agency=agency, phone=phone)
                if row[EMAIL]:
                    email = EmailAddress.objects.fetch(row[EMAIL])
                    AgencyEmail.objects.get_or_create(
                        agency=agency,
                        email=email,
                        request_type="primary",
                        email_type="to",
                    )
