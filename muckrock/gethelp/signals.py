"""Signal handlers for the gethelp app"""

# Django
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

# MuckRock
from muckrock.gethelp.models import Category, Problem
from muckrock.gethelp.utils import bust_cache


@receiver([post_save, post_delete], sender=Category)
@receiver([post_save, post_delete], sender=Problem)
def invalidate_problems_cache(**kwargs):
    bust_cache()
