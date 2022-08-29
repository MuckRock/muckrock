"""Rules based permissions for the crowdsource app"""

# pylint: disable=unused-argument, invalid-unary-operand-type

# Third Party
from rules import add_perm, always_deny, is_staff, predicate

# MuckRock
from muckrock.foia.rules import has_feature_level, skip_if_not_obj, user_authenticated


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
    return crowdsource.project and crowdsource.project.has_contributor(user)


@predicate
@skip_if_not_obj
@user_authenticated
def is_project_admin(user, crowdsource):
    return (
        crowdsource.project_admin
        and crowdsource.project
        and crowdsource.project.has_contributor(user)
    )


@predicate
@skip_if_not_obj
def has_gallery(user, crowdsource):
    return crowdsource.fields.filter(gallery=True).exists()


is_crowdsource_admin = is_owner | is_staff | is_project_admin

can_view = has_gallery | is_crowdsource_admin

add_perm("crowdsource.add_crowdsource", has_feature_level(1) | is_experimental)
add_perm("crowdsource.change_crowdsource", is_crowdsource_admin)
add_perm("crowdsource.view_crowdsource", can_view)
add_perm("crowdsource.delete_crowdsource", always_deny)
add_perm(
    "crowdsource.form_crowdsource",
    ~is_project_only | is_contributor | is_crowdsource_admin,
)


def crowdsource_perm(perm):
    @predicate("crowdsource_perm:{}".format(perm))
    def inner(user, crowdsource_response):
        return user.has_perm("crowdsource.{}_crowdsource".format(perm))

    return inner


@predicate
@skip_if_not_obj
def is_gallery(user, response):
    return response.gallery


add_perm("crowdsource.add_crowdsourceresponse", has_feature_level(1) | is_experimental)
add_perm("crowdsource.change_crowdsourceresponse", crowdsource_perm("change"))
add_perm(
    "crowdsource.view_crowdsourceresponse", is_gallery | crowdsource_perm("change")
)
add_perm("crowdsource.delete_crowdsourceresponse", crowdsource_perm("delete"))
