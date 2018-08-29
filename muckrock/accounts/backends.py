"""
Backend to support OIDC login
"""

# Django
from django.conf import settings

# Standard Library
from collections import namedtuple

# Third Party
from social_core.backends.open_id_connect import OpenIdConnectAuth


class SquareletBackend(OpenIdConnectAuth):
    """Authentication Backend for Squarelet OpenId"""
    # pylint: disable=abstract-method
    name = 'squarelet'
    OIDC_ENDPOINT = settings.SQUARELET_URL + '/openid'

    # Password grant support
    # In order to override as few methods as possible, we pass in the pass grant
    # auth information on an attribute called `password_grant_auth`.  If the
    # attribute is present, we pass in the password grant parameters instead of
    # the authorization code parameters.  It also overrides the nonce check, since
    # that is not used in the password grant flow
    def auth_complete_params(self, state=None):
        """Override this to allow for password grant auth"""
        if hasattr(self, 'password_grant_auth') and self.password_grant_auth:
            client_id, client_secret = self.get_key_and_secret()
            username, password = self.password_grant_auth
            params = {
                'grant_type': 'password',
                'client_id': client_id,
                'client_secret': client_secret,
                'username': username,
                'password': password,
            }
            params.update(self.get_scope_argument())
            return params
        else:
            return super(SquareletBackend, self).auth_complete_params(state)

    # We do not have nonce's in the password grant flow
    def get_nonce(self, nonce):
        if hasattr(self, 'password_grant_auth') and self.password_grant_auth:
            return namedtuple('FakeNonce', ['id'])(id=True)
        else:
            return super(SquareletBackend, self).get_nonce(nonce)

    def remove_nonce(self, nonce_id):
        if hasattr(self, 'password_grant_auth') and self.password_grant_auth:
            return
        else:
            return super(SquareletBackend, self).remove_nonce(nonce_id)
