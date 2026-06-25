"""Factories for the gethelp app"""

# Third Party
import factory

# MuckRock
from muckrock.gethelp.models import Category, Problem


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category
        django_get_or_create = ("label",)

    label = "Managing this request"
    order = 0


class ProblemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Problem

    category = factory.SubFactory(CategoryFactory)
    title = factory.Faker("sentence")
    resolution = ""
    order = factory.Sequence(lambda n: n)
