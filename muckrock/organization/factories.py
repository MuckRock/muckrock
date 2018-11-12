"""
Factories for the organization app
"""
# Django
from django.utils.text import slugify

# Third Party
import factory

# MuckRock
from muckrock.organization.models import Membership, Organization, Plan


class OrganizationFactory(factory.django.DjangoModelFactory):
    """A factory for creating Organization test objects."""

    class Meta:
        model = Organization

    name = factory.Sequence(lambda n: "Organization %d" % n)
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))
    individual = False
    plan = factory.SubFactory('muckrock.organization.factories.FreePlanFactory')


class MembershipFactory(factory.django.DjangoModelFactory):
    """A factory for creating Membership test objects."""

    class Meta:
        model = Membership

    user = factory.SubFactory('muckrock.core.factories.UserFactory')
    organization = factory.SubFactory(
        'muckrock.organization.factories.OrganizationFactory'
    )
    active = True


class PlanFactory(factory.django.DjangoModelFactory):
    """A factory for creating Plan test objects"""

    class Meta:
        model = Plan
        django_get_or_create = ('name',)

    name = factory.Sequence(lambda n: "Plan %d" % n)
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))


class FreePlanFactory(PlanFactory):
    """A free plan factory"""
    name = 'Free'


class ProfessionalPlanFactory(PlanFactory):
    """A professional plan factory"""
    name = 'Professional'
    minimum_users = 1
    base_requests = 20
    feature_level = 1


class OrganizationPlanFactory(PlanFactory):
    """An organization plan factory"""
    name = 'Organization'
    minimum_users = 5
    base_requests = 50
    requests_per_user = 5
    feature_level = 2
