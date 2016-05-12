"""
Factories generate objects during testing
"""

from django.contrib.auth.models import User
from django.utils.text import slugify

import datetime
import factory

from muckrock.accounts.models import Profile, Statistics
from muckrock.agency.models import Agency, STALE_DURATION
from muckrock.foia.models import FOIARequest, FOIACommunication, FOIAFile, RawEmail
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.news.models import Article
from muckrock.organization.models import Organization
from muckrock.project.models import Project
from muckrock.qanda.models import Question, Answer

# pylint:disable=too-many-instance-attributes

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
    days = 20
    level = 'f'


class AgencyFactory(factory.django.DjangoModelFactory):
    """A factory for creating Agency test objects."""
    class Meta:
        model = Agency

    name = factory.Sequence(lambda n: "Agency %d" % n)
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))
    jurisdiction = factory.SubFactory('muckrock.factories.JurisdictionFactory')
    status = 'approved'


class FOIARequestFactory(factory.django.DjangoModelFactory):
    """A factory for creating FOIARequest test objects."""
    class Meta:
        model = FOIARequest

    title = factory.Sequence(lambda n: "FOIA Request %d" % n)
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))
    user = factory.SubFactory(UserFactory)
    jurisdiction = factory.SubFactory('muckrock.factories.JurisdictionFactory')


class FOIACommunicationFactory(factory.django.DjangoModelFactory):
    """A factory for creating FOIARequest test objects."""
    class Meta:
        model = FOIACommunication

    foia = factory.SubFactory(FOIARequestFactory)
    from_who = factory.Sequence(lambda n: "From: %d" % n)
    priv_from_who = 'Test Sender <test@muckrock.com>'
    date = factory.LazyAttribute(lambda obj: datetime.datetime.now())
    rawemail = factory.RelatedFactory('muckrock.factories.RawEmailFactory', 'communication')


class RawEmailFactory(factory.django.DjangoModelFactory):
    """A factory for creating  objects."""
    class Meta:
        model = RawEmail

    communication = factory.SubFactory(FOIACommunicationFactory, rawemail=None)
    raw_email = factory.Faker('paragraph')


class FOIAFileFactory(factory.django.DjangoModelFactory):
    """A factory for creating FOIAFile test objects."""
    class Meta:
        model = FOIAFile

    foia = factory.SubFactory(FOIARequestFactory)
    comm = factory.SubFactory(FOIACommunicationFactory, foia=factory.SelfAttribute('..foia'))
    title = factory.Faker('word')
    ffile = factory.django.FileField(filename=factory.Faker('file_name'))

class ProjectFactory(factory.django.DjangoModelFactory):
    """A factory for creating Project test objects."""
    class Meta:
        model = Project

    title = factory.Sequence(lambda n: "Project %d" % n)
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))


class QuestionFactory(factory.django.DjangoModelFactory):
    """A factory for creating Question test objects."""
    class Meta:
        model = Question

    user = factory.SubFactory(UserFactory)
    title = factory.Sequence(lambda n: "Question %d" % n)
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))
    question = factory.Faker('paragraph')
    date = factory.LazyAttribute(lambda obj: datetime.datetime.now())


class AnswerFactory(factory.django.DjangoModelFactory):
    """A factory for creating Answer test objects."""
    class Meta:
        model = Answer

    user = factory.SubFactory(UserFactory)
    date = factory.LazyAttribute(lambda obj: datetime.datetime.now())
    question = factory.SubFactory(QuestionFactory)
    answer = factory.Faker('paragraph')


class ArticleFactory(factory.django.DjangoModelFactory):
    """A factory for creating Article test objects."""
    class Meta:
        model = Article

    title = factory.Sequence(lambda n: "Article %d" % n)
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))
    summary = factory.Faker('paragraph')
    body = factory.Faker('paragraph')

    @factory.post_generation
    def authors(self, create, extracted, **kwargs):
        """Adds M2M authors"""
        # pylint: disable=unused-argument
        if not create:
            # Simple build, do nothing.
            return
        if extracted:
            # A list of authors were passed in, use them
            for author in extracted:
                self.authors.add(author)
            return
        # In all other cases, add at least one author
        author = UserFactory()
        self.authors.add(author)
        return


class StatisticsFactory(factory.django.DjangoModelFactory):
    """A factory for creating Statistics test objects."""
    class Meta:
        model = Statistics

    date = factory.LazyAttribute(lambda obj: datetime.date.today())
    total_requests = 42
    total_requests_success = 4
    total_requests_denied = 2
    total_requests_submitted = 8
    requests_processing_days = 10
    total_unresolved_orphan_tasks = 3
    total_pages = 23
    total_fees = 0
    total_users = 24
    pro_users = 2
    total_agencies = 12
    stale_agencies = 4
    unapproved_agencies = 2
    total_tasks = 100
    total_unresolved_tasks = 45
    daily_robot_response_tasks = 12

# Stale Agency Factory

class StaleAgencyFactory(AgencyFactory):
    """A factory for creating stale Agency test objects."""
    stale = True
    stale_foia = factory.RelatedFactory('muckrock.factories.StaleFOIARequestFactory', 'agency')


class StaleFOIARequestFactory(FOIARequestFactory):
    """A factory for creating stale FOIARequest test objects."""
    status = 'ack'
    stale_comm = factory.RelatedFactory('muckrock.factories.StaleFOIACommunicationFactory', 'foia')


class StaleFOIACommunicationFactory(FOIACommunicationFactory):
    """A factory for creating stale FOIARequest test objects."""
    response = True
    date = factory.LazyAttribute(
        lambda obj: datetime.datetime.now() - datetime.timedelta(STALE_DURATION + 1)
    )
