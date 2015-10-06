"""
Factories generate objects during testing
"""

from django.contrib.auth.models import User
from django.utils.text import slugify

import datetime
import factory

from muckrock.accounts.models import Profile
from muckrock.foia.models import FOIARequest
from muckrock.jurisdiction.models import Jurisdiction


class ProfileFactory(factory.django.DjangoModelFactory):
    """A factory for creating Profile test objects."""
    class Meta:
        model = Profile

    user = factory.SubFactory('app.factories.UserFactory', profile=None)
    acct_type = 'community'
    date_update = datetime.datetime.now()


class UserFactory(factory.django.DjangoModelFactory):
    """A factory for creating User test objects."""
    class Meta:
        model = User

    username = factory.Sequence(lambda n: "user_%d" % n)
    profile = factory.RelatedFactory(ProfileFactory, 'user')


class JurisdictionFactory(factory.django.DjangoModelFactory):
    """A factory for creating Jurisdiction test objects."""
    class Meta:
        model = Jurisdiction

    name = factory.Sequence(lambda n: "Jurisdiction %d" % n)
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))


class FOIARequestFactory(factory.django.DjangoModelFactory):
    """A factory for creating FOIARequest test objects."""
    class Meta:
        model = FOIARequest

    title = factory.Sequence(lambda n: "FOIA Request %d" % n)
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))
    user = factory.SubFactory(UserFactory)
    jurisdiction = factory.SubFactory(JurisdictionFactory)
