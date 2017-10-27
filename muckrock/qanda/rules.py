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

@predicate
@user_authenticated
def made_request(user):
    return user.foiarequest_set.exclude(status='started').exists()

add_perm('qanda.post', made_request | is_advanced)
add_perm('qanda.block', is_staff)
