"""
Factories for the Jurisdiction application
"""
# Django
from django.utils.text import slugify

# Third Party
import factory

from .models import (
    Appeal,
    ExampleAppeal,
    Exemption,
    InvokedExemption,
    Jurisdiction,
    Law,
)


class FederalJurisdictionFactory(factory.django.DjangoModelFactory):
    """Federal jurisdiction factory"""

    class Meta:
        model = Jurisdiction

    name = "United States of America"
    abbrev = "USA"
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))
    level = "f"
    law = factory.RelatedFactory(
        "muckrock.jurisdiction.factories.LawFactory", "jurisdiction"
    )


class StateJurisdictionFactory(factory.django.DjangoModelFactory):
    """State jurisdiction factory, always has FederalJurisdictionFactory as parent."""

    class Meta:
        model = Jurisdiction

    name = "Massachusetts"
    abbrev = "MA"
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))
    level = "s"
    parent = factory.SubFactory(FederalJurisdictionFactory)
    law = factory.RelatedFactory(
        "muckrock.jurisdiction.factories.LawFactory", "jurisdiction"
    )


class LocalJurisdictionFactory(factory.django.DjangoModelFactory):
    """Local jurisdiction factory, always has StateJurisdictionFactory as parent."""

    class Meta:
        model = Jurisdiction

    name = "Boston"
    slug = factory.LazyAttribute(
        lambda obj: slugify(obj.name) + "-" + slugify(obj.parent.abbrev)
    )
    level = "l"
    parent = factory.SubFactory(StateJurisdictionFactory)


class LawFactory(factory.django.DjangoModelFactory):
    """State FOI law factory"""

    class Meta:
        model = Law

    jurisdiction = factory.SubFactory(StateJurisdictionFactory, law=None)
    name = "Massachusetts Public Records Law"
    citation = "Massachusetts General Laws, Part 1, Title X, Chapter 66"
    url = "https://malegislature.gov/Laws/GeneralLaws/PartI/TitleX/Chapter66"
    days = 20


class ExemptionFactory(factory.django.DjangoModelFactory):
    """Exemption factory"""

    class Meta:
        model = Exemption

    name = "Public Employment Applications"
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))
    jurisdiction = factory.SubFactory(
        StateJurisdictionFactory, name="Washington", abbrev="WA"
    )
    basis = factory.Faker("paragraph")


class InvokedExemptionFactory(factory.django.DjangoModelFactory):
    """InvokedExemption factory"""

    class Meta:
        model = InvokedExemption

    exemption = factory.SubFactory(ExemptionFactory)
    request = factory.SubFactory("muckrock.foia.factories.FOIARequestFactory")


class ExampleAppealFactory(factory.django.DjangoModelFactory):
    """ExampleAppeal factory"""

    class Meta:
        model = ExampleAppeal

    title = factory.Faker("words")
    language = factory.Faker("paragraph")
    context = factory.Faker("paragraph")
    exemption = factory.SubFactory(ExemptionFactory)


class AppealFactory(factory.django.DjangoModelFactory):
    """Appeal factory"""

    class Meta:
        model = Appeal

    communication = factory.SubFactory(
        "muckrock.foia.factories.FOIACommunicationFactory"
    )
