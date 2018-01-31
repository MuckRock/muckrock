"""Rules based permissions for the Q&A app"""

# pylint: disable=missing-docstring

# needed for rules
from __future__ import absolute_import

# Third Party
from rules import add_perm, predicate

# MuckRock
from muckrock.foia.rules import is_advanced, is_staff, user_authenticated


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
