"""URL configuration for the gethelp app"""

# Django
from django.urls import path

# MuckRock
from muckrock.gethelp import views

urlpatterns = [
    path("contact/", views.contact, name="gethelp-contact"),
]
