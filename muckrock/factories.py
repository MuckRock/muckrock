"""
Factories generate objects during testing
"""

from django.contrib.auth.models import User
from django.utils.text import slugify

import datetime
import factory

from muckrock.accounts.models import Profile
from muckrock.agency.models import Agency
from muckrock.foia.models import FOIARequest, FOIACommunication
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.project.models import Project
from muckrock.organization.models import Organization

class ProfileFactory(factory.django.DjangoModelFactory):
    """A factory for creating Profile test objects."""
    class Meta:
        model = Profile

    user = factory.SubFactory('muckrock.factories.UserFactory', profile=None)
    acct_type = 'basic'
    date_update = datetime.datetime.now()


class UserFactory(factory.django.DjangoModelFactory):
    """A factory for creating User test objects."""
    class Meta:
        model = User

    username = factory.Sequence(lambda n: "user_%d" % n)
    email = factory.Faker('email')
    profile = factory.RelatedFactory(ProfileFactory, 'user')


class OrganizationFactory(factory.django.DjangoModelFactory):
    """A factory for creating Organization test objects."""
    class Meta:
        model = Organization

    name = factory.Sequence(lambda n: "Organization %d" % n)
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))
    owner = factory.SubFactory(UserFactory)


class JurisdictionFactory(factory.django.DjangoModelFactory):
    """A factory for creating Jurisdiction test objects."""
    class Meta:
        model = Jurisdiction

    name = factory.Sequence(lambda n: "Jurisdiction %d" % n)
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))
    level = 'f'


class AgencyFactory(factory.django.DjangoModelFactory):
    """A factory for creating Agency test objects."""
    class Meta:
        model = Agency

    name = factory.Sequence(lambda n: "Agency %d" % n)
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))
    jurisdiction = factory.SubFactory(JurisdictionFactory)
    status = 'approved'


class FOIARequestFactory(factory.django.DjangoModelFactory):
    """A factory for creating FOIARequest test objects."""
    class Meta:
        model = FOIARequest

    title = factory.Sequence(lambda n: "FOIA Request %d" % n)
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))
    user = factory.SubFactory(UserFactory)
    jurisdiction = factory.SubFactory(JurisdictionFactory)


class FOIACommunicationFactory(factory.django.DjangoModelFactory):
    """A factory for creating FOIARequest test objects."""
    class Meta:
        model = FOIACommunication

    foia = factory.SubFactory(FOIARequestFactory)
    from_who = factory.Sequence(lambda n: "From: %d" % n)
    priv_from_who = 'Test Sender <test@muckrock.com>'
    date = factory.LazyAttribute(lambda obj: datetime.datetime.now())


class ProjectFactory(factory.django.DjangoModelFactory):
    """A factory for creating Project test objects."""
    class Meta:
        model = Project

    title = factory.Sequence(lambda n: "Project %d" % n)
