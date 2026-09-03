# -*- coding: utf-8 -*-
"""
Split legacy review agency tasks into one task per broken channel

Existing tasks are keyed on (agency, source) and do not record which channel
triggered them, so a task cannot tell a staffer what is actually broken.  This
emits one task per channel carrying blocked active traffic -- strategy 3 from
the design -- which shrinks the queue rather than exploding it.

Written as a command rather than a data migration because it needs dry-run
output, re-runnability, and a staged production run, none of which a migration
gives us.

Runs only after merge_email_addresses has been applied: with one row per real
mailbox, one task per candidate channel is already one task per mailbox, and
this command needs no case logic of its own.
"""

# Django
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models.functions import Lower

# MuckRock
from muckrock.communication.models import EmailAddress
from muckrock.task.channels import agency_channels
from muckrock.task.models import ReviewAgencyTask


class Command(BaseCommand):
    """Split legacy review agency tasks per channel"""

    help = (
        "Split open review agency tasks into one task per channel carrying "
        "blocked active traffic. Use --dry-run to print the plan."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would be split without writing anything",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        self._assert_addresses_are_merged()

        # Only tasks in the old shape: an open task with no channel.  A task
        # that already names a channel needs no splitting.
        legacy = (
            ReviewAgencyTask.objects.filter(resolved=False, email__isnull=True)
            .select_related("agency")
            .order_by("pk")
        )

        split = 0
        created = 0
        emptied = 0
        for task in legacy:
            channels = [
                channel
                for channel in agency_channels(task.agency)
                if channel.blocked_count > 0
            ]
            if not channels:
                # Zero active is a triage hint, not evidence the agency is
                # abandoned -- the original is closed with a note, and the
                # next request in will open a fresh channel scoped task.
                emptied += 1
                self.stdout.write(
                    f"  task {task.pk} ({task.agency}): no active channels"
                )
                if not dry_run:
                    self._close_original(task, [])
                continue

            self.stdout.write(
                "  task %d (%s): %d channel(s) -> %s"
                % (
                    task.pk,
                    task.agency,
                    len(channels),
                    ", ".join(
                        "%s (%d blocked)"
                        % (channel.address.email, channel.blocked_count)
                        for channel in channels
                    ),
                )
            )
            if not dry_run:
                created += self._split(task, channels)
            else:
                created += len(channels)
            split += 1

        verb = "would split" if dry_run else "split"
        self.stdout.write(
            self.style.SUCCESS(
                f"{verb} {split} task(s) into {created} channel task(s); "
                f"{emptied} had no active channels"
            )
        )

    def _assert_addresses_are_merged(self):
        """Refuse to run while a case variant is still in the table

        One mailbox spread across rows would become several tasks here, which
        is exactly the split the merge exists to prevent.
        """
        unmerged = EmailAddress.objects.exclude(email=Lower("email"))
        count = unmerged.count()
        if count:
            examples = ", ".join(unmerged.values_list("email", flat=True)[:5])
            raise CommandError(
                f"{count} email address(es) are not lowercase (e.g. {examples}). "
                "Run merge_email_addresses first -- splitting now would create "
                "several tasks for one mailbox."
            )

    def _split(self, task, channels):
        """Emit one task per channel and close the original"""
        with transaction.atomic():
            successors = []
            for channel in channels:
                successor = ReviewAgencyTask.objects.create(
                    agency=task.agency,
                    source=task.source,
                    email=channel.address,
                    resolved=False,
                )
                # date_created is auto_now_add, so it has to be set after the
                # insert.  Preserved because task age is a triage signal and
                # resetting it would make an old backlog look brand new.
                ReviewAgencyTask.objects.filter(pk=successor.pk).update(
                    date_created=task.date_created
                )
                successors.append(successor)
            self._close_original(task, successors)
            return len(successors)

    @staticmethod
    def _close_original(task, successors):
        """Resolve the original, noting where the work went.  Never delete."""
        if successors:
            note = "Split into per-channel tasks: " + ", ".join(
                "#%d (%s)" % (successor.pk, successor.email.email)
                for successor in successors
            )
        else:
            note = (
                "Closed by the per-channel split: no channel at this agency is "
                "carrying blocked active requests."
            )
        task.note = "\n".join(filter(None, [task.note, note]))
        task.resolve(None, {"split": note})
