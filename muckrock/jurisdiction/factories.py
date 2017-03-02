"""
Factories for the Jurisdiction application
"""
from django.utils.text import slugify

import factory

from .models import Jurisdiction, Law, Exemption, InvokedExemption, ExampleAppeal, Appeal

class FederalJurisdictionFactory(factory.django.DjangoModelFactory):
    """Federal jurisdiction factory"""
    class Meta:
        model = Jurisdiction

    name = u'United States of America'
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))
    days = 20
    level = 'f'
    intro = factory.Faker('sentence')
    law_name = factory.Faker('word')
    waiver = factory.Faker('paragraph')


class StateJurisdictionFactory(factory.django.DjangoModelFactory):
    """State jurisdiction factory, always has FederalJurisdictionFactory as parent."""
    class Meta:
        model = Jurisdiction

    name = u'Massachusetts'
    abbrev = u'MA'
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))
    days = 20
    level = 's'
    parent = factory.SubFactory(FederalJurisdictionFactory)
    intro = factory.Faker('sentence')
    law_name = factory.Faker('word')
    waiver = factory.Faker('paragraph')


class LocalJurisdictionFactory(factory.django.DjangoModelFactory):
    """Local jurisdiction factory, always has StateJurisdictionFactory as parent."""
    class Meta:
        model = Jurisdiction

    name = u'Boston'
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name) + '-' + slugify(obj.parent.abbrev))
    days = 20
    level = 'l'
    parent = factory.SubFactory(StateJurisdictionFactory)


class LawFactory(factory.django.DjangoModelFactory):
    """State FOI law factory"""
    class Meta:
        model = Law

    jurisdiction = factory.SubFactory(StateJurisdictionFactory)
    name = u'Massachusetts Public Records Law'
    citation = u'Massachusetts General Laws, Part 1, Title X, Chapter 66'
    url = u'https://malegislature.gov/Laws/GeneralLaws/PartI/TitleX/Chapter66'
    summary = u'Passed in 1973, Reform bill signed into law 2015.'


class ExemptionFactory(factory.django.DjangoModelFactory):
    """Exemption factory"""
    class Meta:
        model = Exemption

    name = 'Public Employment Applications'
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))
    jurisdiction = factory.SubFactory(StateJurisdictionFactory, name=u'Washington', abbrev=u'WA')
    basis = factory.Faker('paragraph')


class InvokedExemptionFactory(factory.django.DjangoModelFactory):
    """InvokedExemption factory"""
    class Meta:
        model = InvokedExemption

    exemption = factory.SubFactory(ExemptionFactory)
    request = factory.SubFactory('muckrock.factories.FOIARequestFactory')


class ExampleAppealFactory(factory.django.DjangoModelFactory):
    """ExampleAppeal factory"""
    class Meta:
        model = ExampleAppeal

    title = factory.Faker('words')
    language = factory.Faker('paragraph')
    context = factory.Faker('paragraph')
    exemption = factory.SubFactory(ExemptionFactory)


class AppealFactory(factory.django.DjangoModelFactory):
    """Appeal factory"""
    class Meta:
        model = Appeal

    communication = factory.SubFactory('muckrock.factories.FOIACommunicationFactory')
