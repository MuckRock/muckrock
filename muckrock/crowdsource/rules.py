"""Rules based permissions for the crowdsource app"""

# pylint: disable=missing-docstring
# pylint: disable=unused-argument

# needed for rules
from __future__ import absolute_import

# Third Party
from rules import add_perm, predicate

# MuckRock
from muckrock.foia.rules import is_advanced, user_authenticated


@predicate
@user_authenticated
def is_experimental(user):
    return user.profile.experimental


add_perm('crowdsource.add_crowdsource', is_advanced | is_experimental)
