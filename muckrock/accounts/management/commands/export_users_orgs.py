"""
Management command to export users and organizations for squarelet
"""
# Django
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

# Third Party
import unicodecsv as csv
from boto.s3.connection import S3Connection
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
        conn = S3Connection(
            settings.AWS_ACCESS_KEY_ID,
            settings.AWS_SECRET_ACCESS_KEY,
        )
        self.bucket = conn.get_bucket(settings.AWS_STORAGE_BUCKET_NAME)
        with transaction.atomic():
            self.export_users()
            self.export_orgs()
            self.export_members()

    def export_users(self):
        """Export users"""
        key = self.bucket.new_key('squarelet_export/users.csv')
        with smart_open(key, 'wb') as out_file:
            writer = csv.writer(out_file)
            writer.writerow([
                'uuid',
                'username',
                'email',
                'password',
                'full_name',
                'is_staff',
                'is_active',
                'is_superuser',
                'email_confirmed',
                'email_failed',
                'is_agency',
                'avatar_url',
                'use_autologin',
                'source',
            ])
            for user in User.objects.select_related('profile'):
                writer.writerow([
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
                    user.profile.avatar.url,
                    user.profile.use_autologin,
                    'muckrock',
                ])

    def export_orgs(self):
        """Export organizations"""
        # pylint: disable=protected-access
        key = self.bucket.new_key('squarelet_export/orgs.csv')
        with smart_open(key, 'wb') as out_file:
            writer = csv.writer(out_file)
            writer.writerow([
                'uuid',
                'name',
                'type',
                'individual',
                'private',
                'customer_id',
                'subscription_id',
                'payment_failed',
                'date_update',
                'max_users',
                'requests_per_month',
                'monthly_requests',
                'number_requests',
            ])
            for org in Organization.objects.select_related(
                'owner__profile'
            ).exclude(
                individual=True, users__profile__acct_type='agency'
            ):
                writer.writerow([
                    org.uuid,
                    org.name,
                    org.plan,
                    org.individual,
                    org.private,
                    org.owner.profile.customer_id,
                    org.stripe_id,
                    org.owner.profile.payment_failed,
                    org.date_update,
                    org.max_users,
                    org.requests_per_month,
                    org.monthly_requests,
                    org.number_requests,
                ])

    def export_members(self):
        """Export memberships"""
        key = self.bucket.new_key('squarelet_export/members.csv')
        with smart_open(key, 'wb') as out_file:
            writer = csv.writer(out_file)
            writer.writerow([
                'user_uuid',
                'org_uuid',
                'user_username',
                'org_name',
                'is_admin',
            ])
            for member in Membership.objects.select_related(
                'user__profile', 'organization'
            ):
                writer.writerow([
                    member.user.profile.uuid,
                    member.organization.uuid,
                    member.user.username,
                    member.organization.name,
                    member.organization.owner == member.user,
                ])
