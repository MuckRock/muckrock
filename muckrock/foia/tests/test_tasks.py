# Django
from django.conf import settings
from django.db import connection, reset_queries
from django.test import TestCase

# MuckRock
from muckrock.core.factories import UserFactory
from muckrock.foia.factories import FOIARequestFactory
from muckrock.foia.tasks import ExportCsv


class ExportCsvTests(TestCase):

    def test_db_calls(self):
        user = UserFactory()

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
