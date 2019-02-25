"""Rules based permissions for the Organization app"""

# pylint: disable=missing-docstring
# pylint: disable=unused-argument

# needed for rules
from __future__ import absolute_import

# Third Party
from rules import add_perm, predicate

# MuckRock
from muckrock.foia.rules import is_staff, user_authenticated


@predicate
def private(user, org):
    return org.private


@predicate
@user_authenticated
def is_member(user, org):
    return org.has_member(user)


add_perm('organization.view', ~private | is_staff | is_member)
