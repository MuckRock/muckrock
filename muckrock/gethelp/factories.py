"""Factories for the gethelp app"""

import factory

from muckrock.gethelp.models import Problem


class ProblemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Problem

    category = "managing"
    title = factory.Faker("sentence")
    resolution = ""
    order = factory.Sequence(lambda n: n)
