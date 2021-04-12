"""
Management command to export users and organizations for squarelet
"""
# Django
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

# Standard Library
import csv

# Third Party
from smart_open.smart_open_lib import smart_open

# MuckRock
from muckrock.organization.models import Membership, Organization


class Command(BaseCommand):
    """
    Command to export all users and organizations for importing into squarelet

    This is intended to be a one time use script for the initial migration to
    squarelet
    """

    def handle(self, *args, **kwargs):
        # pylint: disable=unused-argument
        # pylint: disable=attribute-defined-outside-init
        self.bucket = settings.AWS_STORAGE_BUCKET_NAME
        if kwargs["date_joined"]:
            with transaction.atomic():
                self.export_date_joined()
        else:
            with transaction.atomic():
                self.export_users()
                self.export_orgs()
                self.export_members()

    def add_arguments(self, parser):
        parser.add_argument(
            "--date_joined", action="store_true", help="Only export date joined data"
        )

    def export_users(self):
        """Export users"""
        print("Begin User Export - {}".format(timezone.now()))
        key = f"s3://{self.bucket}/squarelet_export/users.csv"
        with smart_open(key, "wb") as out_file:
            writer = csv.writer(out_file)
            writer.writerow(
                [
                    "uuid",
                    "username",
                    "email",
                    "password",
                    "full_name",
                    "is_staff",
                    "is_active",
                    "is_superuser",
                    "email_confirmed",
                    "email_failed",
                    "is_agency",
                    "avatar_url",
                    "use_autologin",
                    "source",
                ]
            )
            total = User.objects.count()
            for i, user in enumerate(
                User.objects.select_related("profile").prefetch_related(
                    "receipt_emails"
                )
            ):
                if i % 1000 == 0:
                    print("User {} / {} - {}".format(i, total, timezone.now()))
                writer.writerow(
                    [
                        user.profile.uuid,
                        user.username,
                        user.email,
                        user.password,
                        user.profile.full_name,
                        user.is_staff,
                        user.is_active,
                        user.is_superuser,
                        user.profile.email_confirmed,
                        user.profile.email_failed,
                        user.profile.agency is not None,
                        user.profile.avatar.name if user.profile.avatar else "",
                        user.profile.use_autologin,
                        "muckrock",
                    ]
                )
        print("End User Export - {}".format(timezone.now()))

    def export_orgs(self):
        """Export organizations"""
        # pylint: disable=protected-access
        print("Begin Organization Export - {}".format(timezone.now()))
        key = f"s3://{self.bucket}/squarelet_export/orgs.csv"
        with smart_open(key, "wb") as out_file:
            writer = csv.writer(out_file)
            writer.writerow(
                [
                    "uuid",
                    "name",
                    "slug",
                    "entitlement",
                    "individual",
                    "private",
                    "customer_id",
                    "subscription_id",
                    "payment_failed",
                    "date_update",
                    "max_users",
                    "receipt_emails",
                    "avatar_url",
                ]
            )
            total = Organization.objects.count()
            customer_ids = set()
            for i, org in enumerate(
                Organization.objects.select_related(
                    "owner__profile", "entitlement"
                ).prefetch_related("owner__receipt_emails", "owner__organization_set")
            ):
                if i % 1000 == 0:
                    print("Organization {} / {} - {}".format(i, total, timezone.now()))
                if (
                    len(org.owner.organization_set.all()) <= 1 or not org.individual
                ) and not org.owner.profile.customer_id in customer_ids:
                    customer_id = org.owner.profile.customer_id
                    customer_ids.add(customer_id)
                else:
                    customer_id = ""
                writer.writerow(
                    [
                        org.uuid,
                        org.name,
                        org.slug,
                        org.entitlement.slug,
                        org.individual,
                        org.private,
                        customer_id,
                        org.stripe_id,
                        org.owner.profile.payment_failed,
                        org.date_update,
                        org.max_users,
                        ",".join(r.email for r in org.owner.receipt_emails.all()),
                        org.owner.profile.avatar.name if org.individual else "",
                    ]
                )
        print("End Organization Export - {}".format(timezone.now()))

    def export_members(self):
        """Export memberships"""
        print("Begin Membership Export - {}".format(timezone.now()))
        key = f"s3://{self.bucket}/squarelet_export/members.csv"
        with smart_open(key, "wb") as out_file:
            writer = csv.writer(out_file)
            writer.writerow(
                ["user_uuid", "org_uuid", "user_username", "org_name", "is_admin"]
            )
            total = Membership.objects.count()
            for i, member in enumerate(
                Membership.objects.select_related(
                    "user__profile", "organization__owner"
                )
            ):
                if i % 1000 == 0:
                    print("Member {} / {} - {}".format(i, total, timezone.now()))
                writer.writerow(
                    [
                        member.user.profile.uuid,
                        member.organization.uuid,
                        member.user.username,
                        member.organization.name,
                        member.organization.owner == member.user,
                    ]
                )
        print("End Membership Export - {}".format(timezone.now()))

    def export_date_joined(self):
        """Export date joined data"""
        print("Begin Date Joined Export - {}".format(timezone.now()))
        key = f"s3://{self.bucket}/squarelet_export/date_joined.csv"
        with smart_open(key, "wb") as out_file:
            writer = csv.writer(out_file)
            writer.writerow(["uuid", "date_joined"])
            total = User.objects.count()
            for i, user in enumerate(User.objects.select_related("profile")):
                if i % 1000 == 0:
                    print("User {} / {} - {}".format(i, total, timezone.now()))
                writer.writerow([user.profile.uuid, user.date_joined.isoformat()])
        print("End Date Joined Export - {}".format(timezone.now()))
