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
    name = 'squarelet'
    OIDC_ENDPOINT = settings.SQUARELET_URL + '/openid'

    def get_user_details(self, response):
        details = super(SquareletBackend, self).get_user_details(response)
        return details


def save_profile(backend, user, response, *args, **kwargs):
    """Save a profile for new users registered through squarelet"""
    # pylint: disable=unused-argument
    if not hasattr(user, 'profile'):
        Profile.objects.create(
            user=user,
            acct_type='basic',
            email_confirmed=response['email_verified'],
            date_update=date.today(),
        )
