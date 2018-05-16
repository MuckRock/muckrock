"""
Factories for generating FOIA Machine model instances
"""

# Django
from django.utils.text import slugify

# Third Party
import factory

# MuckRock
from muckrock.core import factories as muckrock_factories
from muckrock.foiamachine.models import (
    FoiaMachineCommunication,
    FoiaMachineFile,
    FoiaMachineRequest,
)
from muckrock.jurisdiction import factories as jurisdiction_factories


class FoiaMachineRequestFactory(factory.django.DjangoModelFactory):
    """A factory for creating FoiaMachineRequest objects."""

    class Meta:
        model = FoiaMachineRequest

    title = factory.Sequence(lambda n: "FOIA Machine Request %d" % n)
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))
    user = factory.SubFactory(muckrock_factories.UserFactory)
    jurisdiction = factory.SubFactory(
        jurisdiction_factories.StateJurisdictionFactory
    )
    agency = factory.SubFactory(muckrock_factories.AgencyFactory)


class FoiaMachineCommunicationFactory(factory.django.DjangoModelFactory):
    """A factory for creating FoiaMachineCommunication objects."""

    class Meta:
        model = FoiaMachineCommunication

    request = factory.SubFactory(FoiaMachineRequestFactory)
    sender = factory.Faker('email')
    receiver = factory.Faker('email')
    message = factory.Faker('paragraph')


class FoiaMachineFileFactory(factory.django.DjangoModelFactory):
    """A factory for creating FoiaMachineFile objects."""

    class Meta:
        model = FoiaMachineFile

    communication = factory.SubFactory(FoiaMachineCommunicationFactory)
    file = factory.django.FileField(filename='test_file.txt')
    name = 'test_file.txt'
