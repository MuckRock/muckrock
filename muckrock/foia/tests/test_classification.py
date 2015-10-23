"""
Tests using nose for the classifing of new communications
"""

from django.test import TestCase

import nose.tools

from muckrock.factories import FOIACommunicationFactory
from muckrock.foia.tasks import classify_status
from muckrock.task.models import ResponseTask

class TestFOIAClassify(TestCase):
    """Test the classification of a new communication"""

    def test_classifier(self):
        """Classifier should populate the fields on the response task"""
        # pylint: disable=no-self-use
        comm = FOIACommunicationFactory(
                communication="Here are your responsive documents")
        task = ResponseTask.objects.create(communication=comm)
        classify_status.apply(args=(task.pk,), throw=True)
        task = ResponseTask.objects.get(pk=task.pk)
        nose.tools.ok_(task.predicted_status)
        nose.tools.ok_(task.status_probability)
