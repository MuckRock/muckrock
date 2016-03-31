"""Signals for the task application"""
from django.core.urlresolvers import reverse
from django.db.models.signals import post_save

import logging

from muckrock.message.notifications import SlackNotification
from muckrock.task.models import FlaggedTask, OrphanTask, BlacklistDomain

logger = logging.getLogger(__name__)

def domain_blacklist(sender, instance, created, **kwargs):
    """Blacklist certain domains - automatically reject tasks from them"""
    # pylint: disable=unused-argument
    if not created:
        # if this isn't being created for the first time, just return
        # to avoid an infinite loop from when we resolve the task
        return
    domain = instance.get_sender_domain()
    if domain is None:
        return
    logger.info('Checking domain %s against blacklist', domain)
    if BlacklistDomain.objects.filter(domain=domain).exists():
        instance.resolve()
    return

def notify_flagged(sender, instance, created, **kwargs):
    """When a new flagged task is created, send a Slack notification."""
    # pylint: disable=unused-argument
    if not created or kwargs.get('raw', False):
        # the raw test prevents text fixtures from creating any notifications
        return
    payload = create_flagged_task_payload(instance)
    slack = SlackNotification(payload)
    slack.send()

def create_flagged_task_payload(flagged_task):
    """Create a Slack notification payload for a Flagged Task"""
    base_url = 'https://www.muckrock.com'
    task_url = (base_url + reverse('flagged-task-list') +
            '?id=' + str(flagged_task.id))
    fields = []
    if flagged_task.user is not None:
        author_url = base_url + flagged_task.user.profile.get_absolute_url()
        author_name = flagged_task.user.get_full_name()
        flagged_by = {
            'title': 'Flagged by',
            'value': '<%(user_url)s|%(user_name)s>' % {
                'user_url': author_url,
                'user_name': author_name
            },
            'short': True
        }
        fields.append(flagged_by)
    flagged_object = {
        'title': '%s' % flagged_task.flagged_object().__class__.__name__,
        'value': '<%(url)s|%(name)s>' % {
            'url': base_url + flagged_task.flagged_object().get_absolute_url(),
            'name': unicode(flagged_task.flagged_object())
        },
        'short': True
    }
    fields.append(flagged_object)
    if flagged_task.user is not None:
        created_by = ' by <%(user_url)s|%(user_name)s>' % {
            'user_url': author_url,
            'user_name': author_name,
        }
    else:
        created_by = ''
    summary = (
        'A <%(task_url)s|flagged task> was created%(created_by)s: %(text)s' % {
            'task_url': task_url,
            'created_by': created_by,
            'text': flagged_task.text,
        })
    payload = {
        'icon_emoji': ':triangular_flag_on_post:',
        'channel': '#tasks',
        'text': 'New <%s|flagged task>' % task_url,
        'attachments': [
            {
                'fallback': summary,
                'text': flagged_task.text,
                'fields': fields,
            }
        ]
    }
    return payload

post_save.connect(
    domain_blacklist,
    sender=OrphanTask,
    dispatch_uid='muckrock.task.signals.domain_blacklist')
post_save.connect(
    notify_flagged,
    sender=FlaggedTask,
    dispatch_uid='muckrock.task.signals.notify_flagged')
