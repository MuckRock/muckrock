"""
Testing factories for the communication app
"""

# Django
from django.utils import timezone

# Standard Library
from datetime import timedelta

# Third Party
import factory
import faker.providers.phone_number.en_US as faker_phone

# MuckRock
from muckrock.communication.models import (
    Address,
    EmailAddress,
    EmailCommunication,
    FaxCommunication,
    PhoneNumber,
)

# Monkey patch the faker phone number provider to not produce international numbers
faker_phone.Provider.formats = [
    f for f in faker_phone.Provider.formats if not f.startswith("+")
]


class EmailAddressFactory(factory.django.DjangoModelFactory):
    """A factory for creating email addresses"""

    class Meta:
        model = EmailAddress

    email = factory.Faker("email")
    name = factory.Faker("name")


class PhoneNumberFactory(factory.django.DjangoModelFactory):
    """A factory for creating phone numbers"""

    class Meta:
        model = PhoneNumber

    number = factory.Sequence(lambda n: "617-555-%04d" % n)


class AddressFactory(factory.django.DjangoModelFactory):
    """A factory for creating addresses"""

    class Meta:
        model = Address

    address = factory.Faker("address")


class EmailCommunicationFactory(factory.django.DjangoModelFactory):
    """A factory for creating email communications"""

    class Meta:
        model = EmailCommunication

    communication = factory.SubFactory(
        "muckrock.foia.factories.FOIACommunicationFactory"
    )
    sent_datetime = timezone.now() - timedelta(3)
    from_email = factory.SubFactory(EmailAddressFactory)
    raw_email = factory.RelatedFactory(
        "muckrock.foia.factories.RawEmailFactory", "email"
    )


class FaxCommunicationFactory(factory.django.DjangoModelFactory):
    """A factory for creating fax communications"""

    class Meta:
        model = FaxCommunication

    communication = factory.SubFactory(
        "muckrock.foia.factories.FOIACommunicationFactory"
    )
    sent_datetime = timezone.now() - timedelta(3)
    to_number = factory.SubFactory(PhoneNumberFactory)
