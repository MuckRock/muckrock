"""
URL mappings for mailgun
"""

# Django
from django.urls import re_path

# MuckRock
from muckrock.mailgun import views

urlpatterns = [
    re_path(r"^route/$", views.route_mailgun, name="mailgun-route"),
    re_path(r"^bounces/$", views.bounces, name="mailgun-bounces"),
    re_path(r"^opened/$", views.opened, name="mailgun-opened"),
    re_path(r"^delivered/$", views.delivered, name="mailgun-delivered"),
    re_path(r"^phaxio/$", views.phaxio_callback, name="phaxio-callback"),
]
