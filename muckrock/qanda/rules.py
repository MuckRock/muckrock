"""Rules based permissions for the Q&A app"""

# needed for rules
from __future__ import absolute_import

from rules import (
        add_perm,
        predicate,
        )

from muckrock.foia.rules import (
        user_authenticated,
        is_staff,
        is_advanced,
        )

# pylint: disable=missing-docstring

@predicate
@user_authenticated
def has_confirmed_email(user):
    return user.profile.email_confirmed

@predicate
@user_authenticated
def has_requests(user):
    return user.profile.num_requests > 0

add_perm('qanda.post', has_confirmed_email | has_requests | is_advanced)
add_perm('qanda.block', is_staff)
