"""Celery configuration app"""
# Django
from celery import Celery
from django.conf import settings

# Standard Library
import os

# Third Party
import scout_apm.celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "muckrock.settings.local")

app = Celery("muckrock")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

if settings.USE_SCOUT:
    scout_apm.celery.install(app)
