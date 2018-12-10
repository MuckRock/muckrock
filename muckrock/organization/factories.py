"""
Factories for th eorganization app
"""
# Django
from django.utils.text import slugify

# Third Party
import factory

# MuckRock
from muckrock.organization.models import Membership, Organization


class OrganizationFactory(factory.django.DjangoModelFactory):
    """A factory for creating Organization test objects."""

    class Meta:
        model = Organization

    name = factory.Sequence(lambda n: "Organization %d" % n)
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))
    individual = False
    org_type = 1


class MembershipFactory(factory.django.DjangoModelFactory):
    """A factory for creating Membership test objects."""

    class Meta:
        model = Membership

    user = factory.SubFactory('muckrock.core.factories.UserFactory')
    organization = factory.SubFactory(
        'muckrock.organization.factories.OrganizationFactory'
    )
    active = True
