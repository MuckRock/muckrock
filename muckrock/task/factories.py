"""
Task factories, for testing
"""

import factory

from muckrock.task.models import FlaggedTask

class FlaggedTaskFactory(factory.django.DjangoModelFactory):
    """A factory for creating FlaggedTask objects."""
    class Meta:
        model = FlaggedTask

    user = factory.SubFactory('muckrock.factories.UserFactory')
    foia = factory.SubFactory('muckrock.factories.FOIARequestFactory')
