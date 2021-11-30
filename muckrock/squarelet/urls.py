"""URL mappings for squarelet app"""

# Django
from django.urls import re_path

# MuckRock
from muckrock.squarelet import views

urlpatterns = [re_path(r"^webhook/$", views.webhook, name="squarelet-webhook")]
