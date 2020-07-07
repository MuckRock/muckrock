"""URL mappings for squarelet app"""

# Django
from django.conf.urls import url

# MuckRock
from muckrock.squarelet import views

urlpatterns = [
    url(r"^webhook/$", views.webhook, name="squarelet-webhook"),
]
