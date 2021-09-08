"""
Factories generate objects during testing for the FOIA app
"""

# Django
from django.utils import timezone
from django.utils.text import slugify

# Standard Library
import random
from string import digits

# Third Party
import factory

# MuckRock
from muckrock.communication.models import EmailAddress
from muckrock.foia.models import (
    FOIACommunication,
    FOIAComposer,
    FOIAFile,
    FOIARequest,
    FOIATemplate,
    OutboundRequestAttachment,
    RawEmail,
)


class FOIAComposerFactory(factory.django.DjangoModelFactory):
    """A factory for creating FOIAComposer test objects"""

    class Meta:
        model = FOIAComposer

    user = factory.SubFactory("muckrock.core.factories.UserFactory")
    organization = factory.SubFactory(
        "muckrock.organization.factories.OrganizationFactory"
    )
    title = factory.Sequence("FOIA Composer #{}".format)
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))

    @factory.post_generation
    def agencies(self, create, extracted, **kwargs):
        """Adds M2M agencies"""
        # pylint: disable=unused-argument
        if create and extracted:
            # A list of agencies were passed in, use them
            for agency in extracted:
                self.agencies.add(agency)


class FOIARequestFactory(factory.django.DjangoModelFactory):
    """A factory for creating FOIARequest test objects."""

    # pylint: disable=too-many-instance-attributes

    class Meta:
        model = FOIARequest

    title = factory.Sequence("FOIA Request {}".format)
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))
    agency = factory.SubFactory("muckrock.core.factories.AgencyFactory")
    composer = factory.SubFactory(FOIAComposerFactory)
    email = factory.SubFactory("muckrock.communication.factories.EmailAddressFactory")
    mail_id = factory.Sequence(
        lambda n: "{}-{}".format(n, "".join(random.choice(digits) for _ in range(8)))
    )

    @factory.post_generation
    def cc_emails(self, create, extracted, **kwargs):
        """Adds M2M cc emails"""
        # pylint: disable=unused-argument
        if create and extracted:
            # A list of emails were passed in, use them
            self.cc_emails.set(EmailAddress.objects.fetch_many(extracted))


class FOIACommunicationFactory(factory.django.DjangoModelFactory):
    """A factory for creating FOIARequest test objects."""

    class Meta:
        model = FOIACommunication

    foia = factory.SubFactory(FOIARequestFactory)
    from_user = factory.SubFactory("muckrock.core.factories.UserFactory")
    to_user = factory.SubFactory("muckrock.core.factories.UserFactory")
    datetime = factory.LazyAttribute(lambda obj: timezone.now())
    email = factory.RelatedFactory(
        "muckrock.communication.factories.EmailCommunicationFactory", "communication"
    )
    communication = factory.Faker("paragraph")


class RawEmailFactory(factory.django.DjangoModelFactory):
    """A factory for creating  objects."""

    class Meta:
        model = RawEmail

    email = factory.SubFactory(
        "muckrock.communication.factories.EmailCommunicationFactory"
    )
    raw_email_db = factory.Faker("paragraph")


class FOIAFileFactory(factory.django.DjangoModelFactory):
    """A factory for creating FOIAFile test objects."""

    class Meta:
        model = FOIAFile

    comm = factory.SubFactory(FOIACommunicationFactory)
    title = factory.Faker("word")
    ffile = factory.django.FileField(filename=factory.Faker("file_name"))


class OutboundRequestAttachmentFactory(factory.django.DjangoModelFactory):
    """A factory for creating FOIAFile test objects."""

    class Meta:
        model = OutboundRequestAttachment

    foia = factory.SubFactory(FOIARequestFactory)
    user = factory.SelfAttribute("foia.composer.user")
    ffile = factory.django.FileField(filename=factory.Faker("file_name"))
    date_time_stamp = factory.LazyAttribute(lambda obj: timezone.now())
    sent = False


class FOIATemplateFactory(factory.django.DjangoModelFactory):
    """A factory for creating FOIATemplate test objects"""

    class Meta:
        model = FOIATemplate

    name = factory.Sequence("FOIA Template #{}".format)
    user = factory.SubFactory("muckrock.core.factories.UserFactory")
    template = (
        "To Whom It May Concern:\r\n\r\nPursuant to the { law name }, I "
        "hereby request the following records:\r\n\r\n{ requested docs }\r\n\r\n"
        "{ waiver }\r\n\r\nIn the event that there are fees, I would be grateful if "
        "you would inform me of the total charges in advance of fulfilling my request. "
        "I would prefer the request filled electronically, by e-mail attachment if "
        "available or CD-ROM if not.\r\n\r\nThank you in advance for your anticipated "
        "cooperation in this matter. I look forward to receiving your response to this "
        "request within { days }.\r\n\r\n{ closing }"
    )
