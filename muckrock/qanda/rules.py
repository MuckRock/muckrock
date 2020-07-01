"""Rules based permissions for the Q&A app"""

# pylint: disable=missing-docstring

# needed for rules


# Third Party
from rules import add_perm, predicate

# MuckRock
from muckrock.foia.rules import has_feature_level, is_staff, user_authenticated


@predicate
@user_authenticated
def has_confirmed_email(user):
    return user.profile.email_confirmed


@predicate
@user_authenticated
def made_request(user):
    return user.composers.exclude(status='started').exists()


add_perm('qanda.post', made_request | has_feature_level(1))
add_perm('qanda.block', is_staff)
