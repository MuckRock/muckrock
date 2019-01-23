"""
View mixins
"""

# Django
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User

# Standard Library
import logging
import sys

# Third Party
import requests
from simplejson.scanner import JSONDecodeError

# MuckRock
from muckrock.accounts.models import Profile
from muckrock.accounts.utils import mailchimp_subscribe, mixpanel_event
from muckrock.core.utils import squarelet_post
from muckrock.organization.models import Membership, Organization, Plan

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
                'preferred_username': full_name,
                'email': email,
            },
        )

        user, _ = Profile.objects.squarelet_update_or_create(
            user_json['uuid'], user_json
        )
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


class BuyRequestsMixin(object):
    """Buy requests functionality"""

    def buy_requests(self, form, organization=None, payer=None):
        """Buy requests"""
        if 'organization' in form.cleaned_data:
            organization = payer = form.cleaned_data['organization']
        try:
            num_requests = form.cleaned_data['num_requests']
            price = form.get_price(num_requests)
            payer.pay(
                amount=price,
                description='Purchase {} requests'.format(num_requests),
                token=form.cleaned_data['stripe_token'],
                save_card=form.cleaned_data['save_card'],
            )
            organization.add_requests(num_requests)
        except requests.exceptions.RequestException as exc:
            messages.error(
                self.request, 'Payment Error: {}'.format(
                    '\n'.join(
                        '{}: {}'.format(k, v)
                        for k, v in exc.response.json().iteritems()
                    )
                )
            )
            logger.warn('Payment error: %s', exc, exc_info=sys.exc_info())
            return

        self.request.session['ga'] = 'request_purchase'
        mixpanel_event(
            self.request,
            'Requests Purchased',
            {
                'Number': num_requests,
                'Recipient': organization.name,
                'Price': price / 100,
            },
            charge=price / 100,
        )
        if organization.individual:
            msg = (
                'Purchase successful.  {} requests have been added to your '
                'account.'.format(num_requests)
            )
        else:
            msg = (
                'Purchase successful.  {} requests have been added to '
                '{}\'s account.'.format(num_requests, organization.name)
            )
        messages.success(self.request, msg)
