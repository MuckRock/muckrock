# Django
from django.conf import settings
from django.db import connection, reset_queries
from django.test import TestCase

# Third Party
import boto3
from moto import mock_aws

# MuckRock
from muckrock.core.factories import UserFactory
from muckrock.foia.factories import FOIARequestFactory
from muckrock.foia.tasks import ExportCsv


class ExportCsvTests(TestCase):

    @mock_aws
    def test_db_calls(self):
        user = UserFactory()
        s3 = boto3.client("s3")
        s3.create_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)

        def get_num_queries(batch_size):
            foias = FOIARequestFactory.create_batch(batch_size)

            try:
                settings.DEBUG = True
                reset_queries()
                ExportCsv(user.pk, [f.pk for f in foias]).run()
                num_queries = len(connection.queries)
            finally:
                settings.DEBUG = False
                reset_queries()

            return num_queries

        assert get_num_queries(1) == get_num_queries(10)
