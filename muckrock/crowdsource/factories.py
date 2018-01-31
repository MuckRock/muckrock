"""
Testing factories for the crowdsource app
"""

# Django
from django.utils.text import slugify

# Third Party
import factory

# MuckRock
from muckrock.crowdsource.models import (
    Crowdsource,
    CrowdsourceChoice,
    CrowdsourceData,
    CrowdsourceField,
    CrowdsourceResponse,
    CrowdsourceValue,
)


class CrowdsourceFactory(factory.django.DjangoModelFactory):
    """A factory for creating Crowdsources"""

    class Meta:
        model = Crowdsource

    title = factory.Sequence('Crowdsource #{}'.format)
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))
    user = factory.SubFactory('muckrock.factories.UserFactory')
    description = factory.Faker('sentence')


class CrowdsourceDataFactory(factory.django.DjangoModelFactory):
    """A factory for creating Crowdsource Data"""

    class Meta:
        model = CrowdsourceData

    crowdsource = factory.SubFactory(CrowdsourceFactory)
    url = factory.Faker('url')


class CrowdsourceFieldFactory(factory.django.DjangoModelFactory):
    """A factory for creating Crowdsource Fields"""

    class Meta:
        model = CrowdsourceField

    crowdsource = factory.SubFactory(CrowdsourceFactory)
    label = factory.Sequence('Field #{}'.format)


class CrowdsourceTextFieldFactory(CrowdsourceFieldFactory):
    """A factory for creating a text field"""
    type = 'text'


class CrowdsourceSelectFieldFactory(CrowdsourceFieldFactory):
    """A factory for creating a select field"""
    type = 'select'
    choice0 = factory.RelatedFactory(
        'muckrock.crowdsource.factories.CrowdsourceChoiceFactory',
        'field',
        order=1,
    )
    choice1 = factory.RelatedFactory(
        'muckrock.crowdsource.factories.CrowdsourceChoiceFactory',
        'field',
        order=2,
    )
    choice2 = factory.RelatedFactory(
        'muckrock.crowdsource.factories.CrowdsourceChoiceFactory',
        'field',
        order=3,
    )


class CrowdsourceChoiceFactory(factory.django.DjangoModelFactory):
    """A factory for creating a crowdsource choice"""

    class Meta:
        model = CrowdsourceChoice

    field = factory.SubFactory(CrowdsourceSelectFieldFactory)
    choice = factory.Sequence('Choice #{}'.format)
    value = factory.Sequence('choice-{}'.format)


class CrowdsourceResponseFactory(factory.django.DjangoModelFactory):
    """A factory for creating crowdsource responses"""

    class Meta:
        model = CrowdsourceResponse

    crowdsource = factory.SubFactory(CrowdsourceFactory)
    user = factory.SubFactory('muckrock.factories.UserFactory')
    data = factory.SubFactory(CrowdsourceDataFactory)


class CrowdsourceValueFactory(factory.django.DjangoModelFactory):
    """A factory for creating crowdsource values"""

    class Meta:
        model = CrowdsourceValue

    response = factory.SubFactory(CrowdsourceResponseFactory)
    field = factory.SubFactory(CrowdsourceFieldFactory)
    value = factory.Faker('word')
