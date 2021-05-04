"""
Factories for the organization app
"""
# Django
from django.utils.text import slugify

# Third Party
import factory

# MuckRock
from muckrock.organization.models import Entitlement, Membership, Organization


class OrganizationFactory(factory.django.DjangoModelFactory):
    """A factory for creating Organization test objects."""

    class Meta:
        model = Organization

    name = factory.Sequence(lambda n: "Organization %d" % n)
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))
    individual = False
    entitlement = factory.SubFactory(
        "muckrock.organization.factories.FreeEntitlementFactory"
    )


class MembershipFactory(factory.django.DjangoModelFactory):
    """A factory for creating Membership test objects."""

    class Meta:
        model = Membership

    user = factory.SubFactory("muckrock.core.factories.UserFactory")
    organization = factory.SubFactory(
        "muckrock.organization.factories.OrganizationFactory"
    )
    active = True


class EntitlementFactory(factory.django.DjangoModelFactory):
    """A factory for creating Entitlement test objects"""

    class Meta:
        model = Entitlement
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: "Entitlement %d" % n)
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))


class FreeEntitlementFactory(EntitlementFactory):
    """A free entitlement factory"""

    name = "Free"
    resources = {
        "minimum_users": 1,
        "base_requests": 0,
        "requests_per_user": 0,
        "feature_level": 0,
    }


class ProfessionalEntitlementFactory(EntitlementFactory):
    """A professional entitlement factory"""

    name = "Professional"
    resources = {
        "minimum_users": 1,
        "base_requests": 20,
        "requests_per_user": 0,
        "feature_level": 1,
    }


class OrganizationEntitlementFactory(EntitlementFactory):
    """An organization entitlement factory"""

    name = "Organization"
    resources = {
        "minimum_users": 5,
        "base_requests": 50,
        "requests_per_user": 5,
        "feature_level": 2,
    }
