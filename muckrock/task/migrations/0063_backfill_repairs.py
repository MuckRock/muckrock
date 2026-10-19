"""Record the repairs made before the repair history existed

Built from the outcome each task kept in form_data["repair"].  Those carry no
snapshot of the channel's errors and no follow up links, so the rows are
marked backfilled and the readout says so rather than showing blanks as fact.
"""

# Django
from django.db import migrations
from django.utils.dateparse import parse_datetime


def backfill_repairs(apps, schema_editor):
    """One repair per submission, from the tasks it touched"""
    # pylint: disable=unused-argument
    ReviewAgencyTask = apps.get_model("task", "ReviewAgencyTask")
    ReviewAgencyRepair = apps.get_model("task", "ReviewAgencyRepair")
    EmailAddress = apps.get_model("communication", "EmailAddress")
    User = apps.get_model("auth", "User")

    # A multi channel submission wrote the same user and timestamp onto every
    # task it touched, so those three together identify one submission.
    # Tasks already linked to a repair are skipped, so this can run again.
    groups = {}
    tasks = (
        ReviewAgencyTask.objects.filter(form_data__has_key="repair", repairs=None)
        .order_by("pk")
        .iterator()
    )
    for task in tasks:
        outcome = task.form_data["repair"] or {}
        key = (task.agency_id, outcome.get("by"), outcome.get("at"))
        groups.setdefault(key, []).append((task, outcome))

    users = {}
    for (agency_id, username, at), members in groups.items():
        if username not in users:
            users[username] = (
                User.objects.filter(username=username).first() if username else None
            )
        first = members[0][1]
        new_email = first.get("new_email")
        repair = ReviewAgencyRepair.objects.create(
            agency_id=agency_id,
            user=users[username],
            datetime=(parse_datetime(at) if at else None)
            or members[0][0].date_done
            or members[0][0].date_created,
            # Never minted here: an address missing from the table stays a
            # string in the snapshot
            new_email=(
                EmailAddress.objects.filter(email__iexact=new_email).first()
                if new_email
                else None
            ),
            snail_mail=bool(first.get("snail_mail")),
            agency_info_updated=bool(first.get("agency_info_updated")),
            followup_sent=bool(first.get("followup_sent")),
            requests_updated=sum(
                outcome.get("requests_updated") or 0 for _task, outcome in members
            ),
            before={
                "backfilled": True,
                "new_email": new_email,
                "channels": [
                    {
                        "email": outcome["old_email"],
                        "requests_moved": outcome.get("requests_updated") or 0,
                    }
                    for _task, outcome in members
                    if outcome.get("old_email")
                ],
            },
        )
        repair.tasks.set([task for task, _outcome in members])


class Migration(migrations.Migration):

    dependencies = [
        ("task", "0062_reviewagencyrepair"),
    ]

    operations = [
        migrations.RunPython(backfill_repairs, migrations.RunPython.noop),
    ]
