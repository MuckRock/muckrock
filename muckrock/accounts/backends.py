"""
Backend to support case insensitive login
http://www.shopfiber.com/case-insensitive-username-login-in-django/
"""

# Django
from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

# Standard Library
from datetime import date

# Third Party
from social_core.backends.open_id_connect import OpenIdConnectAuth

# MuckRock
from muckrock.accounts.models import Profile


class CaseInsensitiveModelBackend(ModelBackend):
    """By default ModelBackend does case _sensitive_ username authentication, which isn't what is
    generally expected.  This backend supports case insensitive username authentication. """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """Authenticate the users case insenstively"""
        # pylint: disable=unused-argument
        try:
            user = User.objects.get(username__iexact=username)
            if user.check_password(password):
                return user
            else:
                return None
        except User.DoesNotExist:
            return None


class SquareletBackend(OpenIdConnectAuth):
    """Authentication Backend for Squarelet OpenId"""
    # pylint: disable=abstract-method
    name = 'squarelet'
    OIDC_ENDPOINT = settings.SQUARELET_URL + '/openid'


def save_profile(backend, user, response, *args, **kwargs):
    """Save a profile for new users registered through squarelet"""
    # pylint: disable=unused-argument
    if not hasattr(user, 'profile'):
        user.profile = Profile(
            user=user,
            acct_type='basic',
            date_update=date.today(),
            uuid=response['uuid'],
        )

    old_email = user.email
    if 'email' in response:
        user.email = response['email']
        user.profile.email_confirmed = response['email_verified']
        if old_email != user.email:
            # if email has changed, update stripe customer and reset email failed flag
            # XXX (do this async?)
            customer = user.profile.customer()
            customer.email = user.email
            customer.save()
            user.profile.email_failed = False

    user.profile.full_name = response['name']
    user.profile.avatar_url = response['picture']

    user.profile.save()
    user.save()
