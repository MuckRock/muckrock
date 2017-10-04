"""
Testing factories for the communication app
"""

from datetime import datetime, timedelta

import factory

from muckrock.communication.models import (
        EmailAddress,
        PhoneNumber,
        Address,
        EmailCommunication,
        FaxCommunication,
        )


class EmailAddressFactory(factory.django.DjangoModelFactory):
    """A factory for creating email addresses"""
    class Meta:
        model = EmailAddress

    email = factory.Faker('email')
    name = factory.Faker('name')


class PhoneNumberFactory(factory.django.DjangoModelFactory):
    """A factory for creating phone numbers"""
    class Meta:
        model = PhoneNumber

    number = factory.Faker('phone_number')


class AddressFactory(factory.django.DjangoModelFactory):
    """A factory for creating addresses"""
    class Meta:
        model = Address

    address = factory.Faker('address')


class EmailCommunicationFactory(factory.django.DjangoModelFactory):
    """A factory for creating email communications"""
    class Meta:
        model = EmailCommunication

    communication = factory.SubFactory(
            'muckrock.factories.FOIACommunicationFactory')
    sent_datetime = datetime.now() - timedelta(3)
    from_email = factory.SubFactory(EmailAddressFactory)
    raw_email = factory.RelatedFactory(
            'muckrock.factories.RawEmailFactory',
            'email',
            )


class FaxCommunicationFactory(factory.django.DjangoModelFactory):
    """A factory for creating fax communications"""
    class Meta:
        model = FaxCommunication

    communication = factory.SubFactory(
            'muckrock.factories.FOIACommunicationFactory')
    sent_datetime = datetime.now() - timedelta(3)
    to_number = factory.SubFactory(PhoneNumberFactory)
