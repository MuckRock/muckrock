"""
Tasks for the notifications application.
"""

import celery

from muckrock.accounts.models import Profile
from muckrock.notification.messages import DailyNotification

@celery.task.periodic_task(run_every=celery.schedules.crontab(hour=10, minute=0),
                           name='muckrock.notification.tasks.daily_notification')
def daily_notification():
    """Send out daily notifications"""
    profiles_to_notify = Profile.objects.filter(email_pref='daily').distinct()
    for profile in profiles_to_notify:
        # for now, only send staff the new updates
        if profile.user.is_staff:
            email = DailyNotification(profile.user)
            email.send(fail_silently=False)
        else:
            profile.send_notifications()
