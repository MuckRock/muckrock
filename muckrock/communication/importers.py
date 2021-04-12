"""
Custom importers for addresses
"""

# Django
from django.conf import settings

# Standard Library
import csv
import re

# Third Party
import boto
from localflavor.us.us_states import STATE_CHOICES

# MuckRock
from muckrock.communication.models import Address

# columns
AGENCY_PK = 0
AGENCY_NAME = 1
ADDRESS_TYPE = 2
ADDRESS_PK = 3
ORIG_ADDRESS = 4
STREET = 5
CITY = 6
STATE = 7
ZIP = 8
LONG = 9
LAT = 10
SUITE = 11
AGENCY_OVERRIDE = 12
ATTN_OVERRIDE = 13

STATES = {s[0] for s in list(STATE_CHOICES)}
p_zip = re.compile(r"^\d{5}(?:-\d{4})?$")

# pylint: disable=broad-except


def import_addresses(file_name):
    """Import addresses from spreadsheet"""
    # pylint: disable=too-many-locals
    conn = boto.connect_s3()
    bucket = conn.get_bucket("muckrock")
    key = bucket.get_key(file_name)
    key.get_contents_to_filename("/tmp/tmp.csv")
    with open("/tmp/tmp.csv") as tmp_file:
        reader = csv.reader(tmp_file)
        # discard header row
        next(reader)
        for i, row in enumerate(reader):
            if i % 1000 == 0:
                print(i)
            if row[STATE] and row[STATE] not in STATES:
                print('Illegal State "{}"'.format(row[STATE]))
            if row[ZIP] and not p_zip.match(row[ZIP]):
                print('Illegal Zip "{}"'.format(row[ZIP]))
            try:
                address = Address.objects.get(pk=row[ADDRESS_PK])
            except Address.DoesNotExist:
                print("Address {} does not exist".format(row[ADDRESS_PK]))
            else:
                address.street = row[STREET].strip()
                address.suite = row[SUITE].strip()
                address.city = row[CITY].strip()
                address.state = row[STATE].strip()
                address.zip_code = row[ZIP].strip()
                address.point = {
                    "type": "Point",
                    "coordinates": [row[LONG].strip(), row[LAT].strip()],
                }
                address.agency_override = row[AGENCY_OVERRIDE].strip()
                address.attn_override = row[ATTN_OVERRIDE].strip()
                try:
                    address.save()
                except Exception as exc:
                    print("Data Error", exc, row[ADDRESS_PK])
                    print(row)
