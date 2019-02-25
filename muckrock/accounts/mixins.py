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
from datetime import date

# Third Party
import requests
import stripe
from simplejson.scanner import JSONDecodeError

# MuckRock
from muckrock.accounts.models import Profile
from muckrock.accounts.utils import (
    get_squarelet_access_token,
    mailchimp_subscribe,
    mixpanel_event,
)
from muckrock.message.tasks import gift

logger = logging.getLogger(__name__)


class MiniregMixin(object):
    """A mixin to expose miniregister functionality to a view"""
    minireg_source = 'Default'
    field_map = {}

    def _create_squarelet_user(self, form, data):
        """Create a corresponding user on squarelet"""

        api_url = '{}/api/users/'.format(settings.SQUARELET_URL)
        access_token = get_squarelet_access_token()
        headers = {'Authorization': 'Bearer {}'.format(access_token)}
        generic_error = (
            'Sorry, something went wrong with the user service.  '
            'Please try again later'
        )

        try:
            resp = requests.post(api_url, data=data, headers=headers)
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
            monthly_requests=settings.MONTHLY_REQUESTS.get('basic', 0),
            date_update=date.today(),
            full_name=full_name,
            uuid=user_json['id'],
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

    def buy_requests(self, form, recipient=None):
        """Buy requests"""
        if recipient is None:
            recipient = self.request.user
        try:
            form.buy_requests(recipient)
        except stripe.StripeError as exc:
            messages.error(self.request, 'Payment Error')
            logger.warn('Payment error: %s', exc, exc_info=sys.exc_info())
            return

        num_requests = form.cleaned_data['num_requests']
        price = form.get_price(num_requests)
        self.request.session['ga'] = 'request_purchase'
        mixpanel_event(
            self.request,
            'Requests Purchased',
            {
                'Number': num_requests,
                'Recipient': recipient.username,
                'Price': price / 100,
            },
            charge=price / 100,
        )
        if recipient == self.request.user:
            msg = (
                'Purchase successful.  {} requests have been added to your '
                'account.'.format(num_requests)
            )
        else:
            msg = (
                'Purchase successful.  {} requests have been gifted to'
                '{}.'.format(num_requests, recipient.profile.full_name)
            )
            gift.delay(
                recipient,
                self.request.user,
                '{} requests'.format(num_requests),
            )
        messages.success(self.request, msg)
