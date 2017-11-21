"""
Custom importers for addresses
"""

from django.conf import settings

import unicodecsv as csv

from boto.s3.connection import S3Connection

from muckrock.communication.models import (
        Address,
        )

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

def import_addresses(file_name):
    """Import addresses from spreadsheet"""
    # pylint: disable=too-many-locals
    conn = S3Connection(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
    bucket = conn.get_bucket('muckrock')
    key = bucket.get_key(file_name)
    key.get_contents_to_filename('/tmp/tmp.csv')
    with open('/tmp/tmp.csv') as tmp_file:
        reader = csv.reader(tmp_file)
        for row in reader:
            try:
                address = Address.objects.get(pk=row[ADDRESS_PK])
            except Address.DoesNotExist:
                print 'Address {} does not exist'.format(row[ADDRESS_PK])
            else:
                address.street = row[STREET]
                address.suite = row[SUITE]
                address.city = row[CITY]
                address.state = row[STATE]
                address.zip_code = row[ZIP]
                address.point = {'type': 'Point', 'coordinates': [row[LONG], row[LAT]]}
                address.agency_override = row[AGENCY_OVERRIDE]
                address.attn_override = row[ATTN_OVERRIDE]
                address.save()
