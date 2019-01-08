"""Rules based permissions for the crowdsource app"""

# pylint: disable=missing-docstring
# pylint: disable=unused-argument

# needed for rules
from __future__ import absolute_import

# Third Party
from rules import add_perm, is_staff, predicate

# MuckRock
from muckrock.foia.rules import (
    has_feature_level,
    skip_if_not_obj,
    user_authenticated,
)


@predicate
@user_authenticated
def is_experimental(user):
    return user.profile.experimental


@predicate
@skip_if_not_obj
@user_authenticated
def is_owner(user, crowdsource):
    return crowdsource.user == user


@predicate
@skip_if_not_obj
def is_project_only(user, crowdsource):
    return crowdsource.project_only and crowdsource.project


@predicate
@skip_if_not_obj
@user_authenticated
def is_contributor(user, crowdsource):
    return crowdsource.project.has_contributor(user)


@predicate
@skip_if_not_obj
@user_authenticated
def is_project_admin(user, crowdsource):
    return (
        crowdsource.project_admin and crowdsource.project
        and crowdsource.project.has_contributor(user)
    )


is_crowdsource_admin = is_owner | is_staff | is_project_admin

add_perm('crowdsource.add_crowdsource', has_feature_level(1) | is_experimental)
add_perm('crowdsource.change_crowdsource', is_crowdsource_admin)
add_perm('crowdsource.view_crowdsource', is_crowdsource_admin)
add_perm(
    'crowdsource.form_crowdsource',
    ~is_project_only | is_contributor | is_crowdsource_admin
)
