"""
View mixins
"""

# Django
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User

# Standard Library
import logging

# Third Party
import requests
from simplejson.scanner import JSONDecodeError

# MuckRock
from muckrock.accounts.models import Profile
from muckrock.accounts.utils import mailchimp_subscribe, mixpanel_event
from muckrock.core.utils import squarelet_post
from muckrock.organization.choices import Plan
from muckrock.organization.models import Membership, Organization

logger = logging.getLogger(__name__)


class MiniregMixin(object):
    """A mixin to expose miniregister functionality to a view"""
    minireg_source = 'Default'
    field_map = {}

    def _create_squarelet_user(self, form, data):
        """Create a corresponding user on squarelet"""

        generic_error = (
            'Sorry, something went wrong with the user service.  '
            'Please try again later'
        )

        try:
            resp = squarelet_post('/api/users/', data=data)
        except requests.exceptions.RequestException:
            form.add_error(None, generic_error)
            raise
        if resp.status_code / 100 != 2:
            try:
                error_json = resp.json()
            except JSONDecodeError:
                form.add_error(None, generic_error)
            else:
                for field, errors in error_json.iteritems():
                    for error in errors:
                        form.add_error(self.field_map.get(field, field), error)
            finally:
                resp.raise_for_status()
        return resp.json()

    def miniregister(self, form, full_name, email, newsletter=False):
        """Create a new user from their full name and email"""
        full_name = full_name.strip()

        user_json = self._create_squarelet_user(
            form,
            {
                'name': full_name,
                'username': full_name,
                'email': email,
            },
        )

        user = User.objects.create_user(
            user_json['username'],
            email,
        )
        Profile.objects.create(
            user=user,
            acct_type='basic',
            full_name=full_name,
            uuid=user_json['id'],
        )
        # XXX how to do this
        org = Organization.objects.create(
            name=user_json['org_name'],
            uuid=user_json['org_uuid'],
            private=True,
            individual=True,
            plan=Plan.free,
        )
        Membership.objects.create(user=user, organization=org, active=True)

        login(
            self.request,
            user,
            backend='muckrock.accounts.backends.SquareletBackend',
        )

        if newsletter:
            mailchimp_subscribe(
                self.request,
                user.email,
                source='Mini-Register: {}'.format(self.minireg_source),
                url='{}{}'.format(settings.MUCKROCK_URL, self.request.path),
            )

        mixpanel_event(
            self.request,
            'Sign Up',
            {
                'Source': 'Mini-Register: {}'.format(self.minireg_source),
                'Newsletter': newsletter,
            },
            signup=True,
        )
        return user
