"""
Factories generate objects during testing
"""

# Django
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify

# Standard Library
import datetime

# Third Party
import factory

# MuckRock
from muckrock.accounts.models import Notification, Profile, Statistics
from muckrock.agency.models import Agency, AgencyEmail, AgencyPhone
from muckrock.communication.models import EmailAddress
from muckrock.crowdfund.models import Crowdfund
from muckrock.news.models import Article
from muckrock.organization.models import Organization
from muckrock.project.models import Project
from muckrock.qanda.models import Answer, Question
from muckrock.utils import new_action


class ProfileFactory(factory.django.DjangoModelFactory):
    """A factory for creating Profile test objects."""

    class Meta:
        model = Profile

    user = factory.SubFactory('muckrock.factories.UserFactory', profile=None)
    acct_type = 'basic'
    date_update = timezone.now()
    customer_id = "cus_RTW3KxBMCknuhB"


class UserFactory(factory.django.DjangoModelFactory):
    """A factory for creating User test objects."""

    class Meta:
        model = User

    username = factory.Sequence(lambda n: "user_%d" % n)
    email = factory.Faker('email')
    profile = factory.RelatedFactory(ProfileFactory, 'user')

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        """Sets password"""
        # pylint: disable=unused-argument
        if extracted:
            self.set_password(extracted)
            self.save()


class NotificationFactory(factory.django.DjangoModelFactory):
    """A factory for creating Notification test objects."""

    class Meta:
        model = Notification

    user = factory.SubFactory(UserFactory)
    action = factory.LazyAttribute(lambda obj: new_action(obj.user, 'acted'))


class OrganizationFactory(factory.django.DjangoModelFactory):
    """A factory for creating Organization test objects."""

    class Meta:
        model = Organization

    name = factory.Sequence(lambda n: "Organization %d" % n)
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))
    owner = factory.SubFactory(UserFactory)


class AgencyFactory(factory.django.DjangoModelFactory):
    """A factory for creating Agency test objects."""

    class Meta:
        model = Agency

    name = factory.Sequence(lambda n: "Agency %d" % n)
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))
    jurisdiction = factory.SubFactory(
        'muckrock.jurisdiction.factories.StateJurisdictionFactory'
    )
    status = 'approved'
    email = factory.RelatedFactory(
        'muckrock.factories.AgencyEmailFactory',
        'agency',
    )
    fax = factory.RelatedFactory(
        'muckrock.factories.AgencyPhoneFactory',
        'agency',
        request_type='primary',
        phone__type='fax',
    )

    @factory.post_generation
    def other_emails(self, create, extracted, **kwargs):
        """Adds M2M other emails"""
        # pylint: disable=unused-argument
        if create and extracted:
            # A list of emails were passed in, use them
            for email in EmailAddress.objects.fetch_many(extracted):
                AgencyEmailFactory(
                    agency=self,
                    email=email,
                    request_type='primary',
                    email_type='cc',
                )


class AgencyEmailFactory(factory.django.DjangoModelFactory):
    """A factory for linking agencies to emails"""

    class Meta:
        model = AgencyEmail

    agency = factory.SubFactory('muckrock.factories.AgencyFactory')
    email = factory.SubFactory(
        'muckrock.communication.factories.EmailAddressFactory'
    )
    request_type = 'primary'
    email_type = 'to'


class AgencyPhoneFactory(factory.django.DjangoModelFactory):
    """A factory for linking agencies to faxes"""

    class Meta:
        model = AgencyPhone

    agency = factory.SubFactory('muckrock.factories.AgencyFactory')
    phone = factory.SubFactory(
        'muckrock.communication.factories.PhoneNumberFactory'
    )
    request_type = 'none'


class AppealAgencyFactory(AgencyFactory):
    """A factory for creating an Agency that accepts email appeals."""
    email = factory.RelatedFactory(
        'muckrock.factories.AgencyEmailFactory',
        'agency',
        request_type='appeal',
    )


class ProjectFactory(factory.django.DjangoModelFactory):
    """A factory for creating Project test objects."""

    class Meta:
        model = Project

    title = factory.Sequence(lambda n: "Project %d" % n)
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))


class CrowdfundFactory(factory.django.DjangoModelFactory):
    """A factory for creating Crowdfund test objects."""

    class Meta:
        model = Crowdfund

    name = factory.Sequence(lambda n: "Crowdfund %d" % n)
    description = factory.Faker('paragraph')
    payment_required = 100.00
    date_due = factory.LazyAttribute(
        lambda obj: datetime.date.today() + datetime.timedelta(30)
    )


class QuestionFactory(factory.django.DjangoModelFactory):
    """A factory for creating Question test objects."""

    class Meta:
        model = Question

    user = factory.SubFactory(UserFactory)
    title = factory.Sequence(lambda n: "Question %d" % n)
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))
    question = factory.Faker('paragraph')
    date = factory.LazyAttribute(lambda obj: timezone.now())


class AnswerFactory(factory.django.DjangoModelFactory):
    """A factory for creating Answer test objects."""

    class Meta:
        model = Answer

    user = factory.SubFactory(UserFactory)
    date = factory.LazyAttribute(lambda obj: timezone.now())
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
    stale_foia = factory.RelatedFactory(
        'muckrock.foia.factories.StaleFOIARequestFactory', 'agency'
    )
