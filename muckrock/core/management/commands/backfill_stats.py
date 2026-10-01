# Django
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

# MuckRock
from muckrock.accounts.stats_api.models import UserStats
from muckrock.organization.models import Organization
from muckrock.organization.stats_api.models import OrganizationStats

BATCH_SIZE = 500


class Command(BaseCommand):
    """Backfill stats rows for existing users and organizations.

    The post_save signals only create rows for records created after deploy, so
    pre-existing users/orgs need rows created here. Idempotent — safe to re-run
    as reconciliation. last_request_at is left null; it populates going forward
    as users file requests (record_request_filed). Individual organizations are
    skipped, matching the signal and the endpoint.
    """

    help = "Create stats rows for existing users and collective organizations"

    def handle(self, *args, **options):
        self._backfill(
            "user",
            User.objects.filter(stats__isnull=True).values_list("pk", flat=True),
            lambda pk: UserStats(user_id=pk),
            UserStats,
        )
        self._backfill(
            "organization",
            Organization.objects.filter(
                individual=False, stats__isnull=True
            ).values_list("pk", flat=True),
            lambda pk: OrganizationStats(organization_id=pk),
            OrganizationStats,
        )

    def _backfill(self, label, pk_iterable, build, model):
        batch = []
        total = 0
        for pk in pk_iterable.iterator(chunk_size=BATCH_SIZE):
            batch.append(build(pk))
            if len(batch) >= BATCH_SIZE:
                model.objects.bulk_create(batch, ignore_conflicts=True)
                total += len(batch)
                batch = []
                self.stdout.write(f"{label}: {total:,} created...")
        if batch:
            model.objects.bulk_create(batch, ignore_conflicts=True)
            total += len(batch)
        self.stdout.write(self.style.SUCCESS(f"{label}: done, {total:,} processed"))
