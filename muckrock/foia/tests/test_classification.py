"""
Tests for the classifing of new communications
"""

# Django
from django.test import TestCase

# Standard Library
from unittest.mock import Mock, patch

# Third Party
from constance.test import override_config

# MuckRock
from muckrock.core.factories import UserFactory
from muckrock.foia.factories import FOIACommunicationFactory, FOIAFileFactory
from muckrock.foia.tasks import classify_status
from muckrock.task.factories import ResponseTaskFactory


def _gloo_result(status):
    """Mock return value for the gloo classifier"""
    return (Mock(trackingNumber=None, price=None, dateEstimate=None), status)


@override_config(ENABLE_GLOO=True, USE_GLOO=True)
class TestFOIAClassify(TestCase):
    """Test the classification of a new communication"""

    @patch("asyncio.run", Mock(return_value=_gloo_result("processed")))
    def test_classifier(self):
        """Classifier should populate the fields on the response task"""
        UserFactory(username="gloo")
        comm = FOIACommunicationFactory(
            communication="Here are your responsive documents"
        )
        task = ResponseTaskFactory(communication=comm)
        classify_status.apply(args=(task.pk,), throw=True)
        task.refresh_from_db()
        assert task.predicted_status == "processed"
        assert task.resolved

    @patch("asyncio.run", Mock(return_value=_gloo_result("processed")))
    def test_classifier_does_not_reopen_closed_request(self):
        """Classifier should not reopen a request which is already closed"""
        UserFactory(username="gloo")
        comm = FOIACommunicationFactory(
            foia__status="done", communication="You're welcome!"
        )
        task = ResponseTaskFactory(communication=comm)
        classify_status.apply(args=(task.pk,), throw=True)
        task.refresh_from_db()
        comm.foia.refresh_from_db()
        assert task.predicted_status == "processed"
        assert not task.resolved
        assert comm.foia.status == "done"

    @patch("asyncio.run", Mock(return_value=_gloo_result("done")))
    def test_classifier_allows_terminal_to_terminal(self):
        """Classifier may move a closed request to another closed status"""
        UserFactory(username="gloo")
        comm = FOIACommunicationFactory(
            foia__status="partial", communication="Here are the rest of the records"
        )
        FOIAFileFactory(comm=comm)
        task = ResponseTaskFactory(communication=comm)
        classify_status.apply(args=(task.pk,), throw=True)
        task.refresh_from_db()
        comm.foia.refresh_from_db()
        assert task.resolved
        assert comm.foia.status == "done"
