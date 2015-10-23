"""
Tests using nose for the classifing of new communications
"""

from django.test import TestCase

import nose.tools

from muckrock.factories import FOIARequestFactory, FOIACommunicationFactory
from muckrock.foia.tasks import classify_status
from muckrock.task.models import ResponseTask

class TestFOIAClassify(TestCase):
    """Test the classification of a new communication"""

    def test_classifier(self):
        """Classifier should populate the fields on the response task"""
        comm = FOIACommunicationFactory(
                communication="Here are your responsive documents")
        task = ResponseTask.objects.create(communication=comm)
        classify_status.apply(args=(task.pk,))
        task = ResponseTask.objects.get(pk=task.pk)
        print task.predicted_status
        print task.status_probability
        nose.tools.ok_(task.predicted_status)
        nose.tools.ok_(task.status_probability)
