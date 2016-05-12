"""
Factories for the Jurisdiction application
"""
from django.utils.text import slugify

import factory

from .models import Jurisdiction

class FederalJurisdictionFactory(factory.django.DjangoModelFactory):
    """Federal jurisdiction factory"""
    class Meta:
        model = Jurisdiction

    name = u'United States of America'
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))
    days = 20
    level = 'f'


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

class LocalJurisdictionFactory(factory.django.DjangoModelFactory):
    """Local jurisdiction factory, always has StateJurisdictionFactory as parent."""
    class Meta:
        model = Jurisdiction

    name = u'Boston'
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name) + '-' + slugify(obj.parent.abbrev))
    days = 20
    level = 'l'
    parent = factory.SubFactory(StateJurisdictionFactory)
