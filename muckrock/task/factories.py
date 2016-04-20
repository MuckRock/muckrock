"""
Task factories, for testing
"""

import factory

from muckrock import task

class OrphanTaskFactory(factory.django.DjangoModelFactory):
    """A factory for creating OrphanTask objects."""
    class Meta:
        model = task.models.OrphanTask

    reason = 'bs'
    communication = factory.SubFactory('muckrock.factories.FOIACommunicationFactory')
    address = factory.Faker('email')


class SnailMailTaskFactory(factory.django.DjangoModelFactory):
    """A factory for creating SnailMailTask objects."""
    class Meta:
        model = task.models.SnailMailTask

    category = 'a'
    communication = factory.SubFactory('muckrock.factories.FOIACommunicationFactory')


class RejectedEmailTaskFactory(factory.django.DjangoModelFactory):
    """A factory for creating RejectedEmailTask objects."""
    class Meta:
        model = task.models.RejectedEmailTask

    category = 'b'
    foia = factory.SubFactory('muckrock.factories.FOIARequestFactory')
    email = factory.Faker('email')


class StaleAgencyTaskFactory(factory.django.DjangoModelFactory):
    """A factory for creating StaleAgencyTask objects."""
    class Meta:
        model = task.models.StaleAgencyTask

    agency = factory.SubFactory('muckrock.factories.StaleAgencyFactory', stale=True)


class FlaggedTaskFactory(factory.django.DjangoModelFactory):
    """A factory for creating FlaggedTask objects."""
    class Meta:
        model = task.models.FlaggedTask

    user = factory.SubFactory('muckrock.factories.UserFactory')
    foia = factory.SubFactory('muckrock.factories.FOIARequestFactory')


class ProjectReviewTaskFactory(factory.django.DjangoModelFactory):
    """A factory for creating ProjectReviewTask objects."""
    class Meta:
        model = task.models.ProjectReviewTask

    project = factory.SubFactory('muckrock.factories.ProjectFactory')
    explanation = factory.Faker('paragraph')


class ResponseTaskFactory(factory.django.DjangoModelFactory):
    """A factory for creating ResponseTask objects."""
    class Meta:
        model = task.models.ResponseTask

    communication = factory.SubFactory('muckrock.factories.FOIACommunicationFactory')


class FailedFaxFactory(factory.django.DjangoModelFactory):
    """A factory for creating FailedFax objects."""
    class Meta:
        model = task.models.FailedFaxTask

    communication = factory.SubFactory('muckrock.factories.FOIACommunicationFactory')


class StatusChangeTaskFactory(factory.django.DjangoModelFactory):
    """A factory for creating StatusChangeTask objects."""
    class Meta:
        model = task.models.StatusChangeTask

    user = factory.SubFactory('muckrock.factories.UserFactory')
    old_status = 'done'
    foia = factory.SubFactory('muckrock.factories.FOIARequestFactory')

