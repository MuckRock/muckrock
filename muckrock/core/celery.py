"""Celery configuration app"""
# Django
from celery import Celery, signals
from django.conf import settings

# Standard Library
import os, logging

# Third Party
import scout_apm.celery

# set the default Django settings module for the 'celery' program.
#  os.environ.setdefault("DJANGO_SETTINGS_MODULE", "muckrock.settings.local")

logger = logging.getLogger(__name__)
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

@signals.task_retry.connect
@signals.task_failure.connect
@signals.task_revoked.connect
def on_task_failure(**kwargs):
    """Abort transaction on task errors.
    """
    # celery exceptions will not be published to `sys.excepthook`. therefore we have to create another handler here.
    from traceback import format_tb

    logger.error('[task:%s:%s]' % (kwargs.get('task_id'), kwargs['sender'].request.correlation_id, )
              + '\n'
              + ''.join(format_tb(kwargs.get('traceback', [])))
              + '\n'
              + str(kwargs.get('exception', '')))
