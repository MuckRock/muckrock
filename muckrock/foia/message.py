"""Notifications for FOIA Requests"""

# MuckRock
from muckrock.message.tasks import slack
from muckrock.message.utils import format_user, slack_attachment, slack_message


def notify_proxy_user(foia):
    """Send a notification that a proxy user was used"""

    proxy_user = slack_attachment("Proxy User", format_user(foia.proxy))
    foia_user = slack_attachment("Requestor", format_user(foia.user))
    summary = f"New <{foia.get_absolute_url()}|proxy request>: {foia.title}"
    attachments = [
        {
            "fallback": summary,
            "text": foia.composer.requested_docs,
            "fields": [proxy_user, foia_user],
        }
    ]
    payload = slack_message(
        ":robot_face:",
        "#proxy",
        f"New <{foia.get_absolute_url()}|proxy request>",
        attachments,
    )

    slack.delay(payload)
