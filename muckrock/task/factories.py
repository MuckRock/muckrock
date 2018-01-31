"""
Task factories, for testing
"""

# Third Party
import factory

# MuckRock
from muckrock import task


class OrphanTaskFactory(factory.django.DjangoModelFactory):
    """A factory for creating OrphanTask objects."""

    class Meta:
        model = task.models.OrphanTask

    reason = 'bs'
    communication = factory.SubFactory(
        'muckrock.factories.FOIACommunicationFactory'
    )
    address = factory.Faker('email')


class SnailMailTaskFactory(factory.django.DjangoModelFactory):
    """A factory for creating SnailMailTask objects."""

    class Meta:
        model = task.models.SnailMailTask

    category = 'a'
    communication = factory.SubFactory(
        'muckrock.factories.FOIACommunicationFactory'
    )


class StaleAgencyTaskFactory(factory.django.DjangoModelFactory):
    """A factory for creating StaleAgencyTask objects."""

    class Meta:
        model = task.models.StaleAgencyTask

    agency = factory.SubFactory(
        'muckrock.factories.StaleAgencyFactory', stale=True
    )


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
    notes = factory.Faker('paragraph')


class NewExemptionTaskFactory(factory.django.DjangoModelFactory):
    """A factory for creating NewExemptionTask objects."""

    class Meta:
        model = task.models.NewExemptionTask

    foia = factory.SubFactory('muckrock.factories.FOIARequestFactory')
    user = factory.SubFactory('muckrock.factories.UserFactory')
    language = factory.Faker('paragraph')


class ResponseTaskFactory(factory.django.DjangoModelFactory):
    """A factory for creating ResponseTask objects."""

    class Meta:
        model = task.models.ResponseTask

    communication = factory.SubFactory(
        'muckrock.factories.FOIACommunicationFactory'
    )


class StatusChangeTaskFactory(factory.django.DjangoModelFactory):
    """A factory for creating StatusChangeTask objects."""

    class Meta:
        model = task.models.StatusChangeTask

    user = factory.SubFactory('muckrock.factories.UserFactory')
    old_status = 'done'
    foia = factory.SubFactory('muckrock.factories.FOIARequestFactory')
