"""Factories for the gethelp app"""

# Third Party
import factory

# MuckRock
from muckrock.gethelp.models import Problem


class ProblemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Problem

    category = "managing"
    title = factory.Faker("sentence")
    resolution = ""
    order = factory.Sequence(lambda n: n)
