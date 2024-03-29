# Generated by Django 4.2 on 2023-10-19 19:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("task", "0053_task_zendesk_ticket_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="flaggedtask",
            name="category",
            field=models.TextField(
                blank=True,
                choices=[
                    (
                        "move communication",
                        "A communication ended up on this request inappropriately.",
                    ),
                    (
                        "no response",
                        "This agency has not responded after multiple submissions.",
                    ),
                    (
                        "wrong agency",
                        "The agency has indicated that this request should be directed to another agency.",
                    ),
                    (
                        "missing documents",
                        "The agency mailed documents but I do not see them on this request",
                    ),
                    ("portal help", "I need help with a portal, link or login"),
                    (
                        "form",
                        "The agency has asked that I fill out or sign a PDF form.",
                    ),
                    (
                        "follow-up complaints",
                        "Agency is complaining about follow-up messages.",
                    ),
                    ("appeal", "Should I appeal this response?"),
                    (
                        "proxy",
                        "The agency denied the request due to an in-state citzenship law.",
                    ),
                    ("contact info changed", "User supplied contact info."),
                    ("no proxy", "No proxy was available."),
                    (
                        "agency login confirm",
                        "An agency used a secure login to update a request.",
                    ),
                    (
                        "agency login validate",
                        "An agency used an insecure login to update a request.",
                    ),
                    (
                        "agency new email",
                        "An agency with no primary email set replied via email.",
                    ),
                    (
                        "manual form",
                        "A request needs a PDF form to be manually filled out to be submitted",
                    ),
                    ("foiaonline", "The FOIAOnline autologin failed"),
                    ("govqa", "The GovQA scraper failed"),
                    (
                        "download file",
                        "This request contains a link to a file to download",
                    ),
                    ("already responded", "I already responded to this request"),
                    ("bad contact", "I am not the best contact for this request"),
                    ("wrong agency", "This request should go to a different agency"),
                ],
            ),
        ),
        migrations.AlterField(
            model_name="responsetask",
            name="predicted_status",
            field=models.CharField(
                blank=True,
                choices=[
                    ("submitted", "Processing"),
                    ("ack", "Awaiting Acknowledgement"),
                    ("processed", "Awaiting Response"),
                    ("appealing", "Awaiting Appeal"),
                    ("fix", "Fix Required"),
                    ("payment", "Payment Required"),
                    ("lawsuit", "In Litigation"),
                    ("rejected", "Rejected"),
                    ("no_docs", "No Responsive Documents"),
                    ("done", "Completed"),
                    ("partial", "Partially Completed"),
                    ("abandoned", "Withdrawn"),
                ],
                max_length=13,
                null=True,
            ),
        ),
    ]
