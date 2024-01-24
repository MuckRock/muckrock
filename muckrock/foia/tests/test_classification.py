"""
Tests using nose for the classifing of new communications
"""

# Django
from django.test import TestCase

# Third Party
import nose.tools
from constance.test import override_config
from mock import Mock, patch

# MuckRock
from muckrock.core.factories import UserFactory
from muckrock.foia.factories import FOIACommunicationFactory
from muckrock.foia.tasks import classify_status
from muckrock.task.factories import ResponseTaskFactory


@override_config(ENABLE_GLOO=True, USE_GLOO=True)
class TestFOIAClassify(TestCase):
    """Test the classification of a new communication"""

    @patch(
        "asyncio.run",
        Mock(
            return_value=(
                Mock(
                    trackingNumber=None,
                    price=None,
                    dateEstimate=None,
                ),
                "processed",
            )
        ),
    )
    def test_classifier(self):
        """Classifier should populate the fields on the response task"""
        UserFactory(username="gloo")
        comm = FOIACommunicationFactory(
            communication="Here are your responsive documents"
        )
        task = ResponseTaskFactory(communication=comm)
        classify_status.apply(args=(task.pk,), throw=True)
        task.refresh_from_db()
        nose.tools.eq_(task.predicted_status, "processed")
        nose.tools.ok_(task.resolved)
