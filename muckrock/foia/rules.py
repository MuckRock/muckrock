"""Rules based permissions for the FOIA app"""

# pylint: disable=missing-docstring, unused-argument, invalid-unary-operand-type

# Django
from django.contrib.auth import load_backend

# Standard Library
import inspect
from datetime import date
from functools import wraps

# Third Party
from rules import add_perm, is_authenticated, is_staff, predicate

# MuckRock
from muckrock.foia.models.request import END_STATUS


def skip_if_not_obj(func):
    """Decorator for predicates
    Skip the predicate if obj is None"""

    @wraps(func)
    def inner(user, obj):
        if obj is None:
            return None
        else:
            return func(user, obj)

    return inner


def user_authenticated(func):
    """Decorator for predicates
    Return false if user is not authenticated"""
    argspec = inspect.getfullargspec(func)
    if len(argspec.args) == 2:

        @wraps(func)
        def inner(user, foia):
            return user.is_authenticated and func(user, foia)

    elif len(argspec.args) == 1:

        @wraps(func)
        def inner(user):
            return user.is_authenticated and func(user)

    return inner


def has_status(*statuses):
    @predicate("has_status:%s" % ",".join(statuses))
    @skip_if_not_obj
    def inner(user, foia):
        return foia.status in statuses

    return inner


@predicate
@skip_if_not_obj
def is_owner(user, foia):
    return foia.user == user


@predicate
@skip_if_not_obj
def is_proxy(user, foia):
    return foia.proxy and foia.proxy == user


@predicate
def no_foia(user, foia):
    return foia is None


@predicate
@skip_if_not_obj
def is_editor(user, foia):
    return user.is_authenticated and foia.edit_collaborators.filter(pk=user.pk).exists()


@predicate
@skip_if_not_obj
def is_read_collaborator(user, foia):
    return user.is_authenticated and foia.read_collaborators.filter(pk=user.pk).exists()


@predicate
@skip_if_not_obj
@user_authenticated
def is_org_shared(user, foia):
    return foia.user.profile.org_share and foia.composer.organization.has_member(user)


is_viewer = is_read_collaborator | is_org_shared


@predicate
@skip_if_not_obj
def is_embargoed(user, foia):
    return foia.embargo


is_private = is_embargoed


@predicate
@skip_if_not_obj
def has_thanks(user, foia):
    return foia.communications.filter(thanks=True).exists()


is_thankable = ~has_thanks & has_status(*END_STATUS)


@predicate
@skip_if_not_obj
def has_appealable_jurisdiction(user, foia):
    return foia.agency and foia.agency.jurisdiction.has_appeal


@predicate
@skip_if_not_obj
def is_overdue(user, foia):
    return foia.date_due is not None and foia.date_due < date.today()


is_appealable = has_appealable_jurisdiction & (
    (has_status("processed", "appealing") & is_overdue)
    | ~has_status("processed", "appealing", "submitted")
)


@predicate
@skip_if_not_obj
def has_crowdfund(user, foia):
    return bool(foia.crowdfund)


@predicate
@skip_if_not_obj
def has_open_crowdfund(user, foia):
    return bool(foia.crowdfund) and not foia.crowdfund.expired()


is_payable = has_status("payment") & ~has_open_crowdfund


@predicate
@skip_if_not_obj
@user_authenticated
def match_agency(user, foia):
    return bool(user.profile.agency and user.profile.agency == foia.agency)


# User predicates


def has_feature_level(level):
    @predicate("has_feature_level:{}".format(level))
    @user_authenticated
    def inner(user):
        return user.profile.feature_level >= level

    return inner


@predicate
@user_authenticated
def is_agency_user(user):
    return user.profile.agency is not None


@predicate
@user_authenticated
def has_perm_embargo(user):
    # we want to directly check the model backend for a permissions to avoid
    # infinite recursion
    backend = load_backend("django.contrib.auth.backends.ModelBackend")
    return backend.has_perm(user, "foia.embargo_perm_foiarequest")


is_from_agency = is_agency_user & match_agency

can_edit = is_owner | is_editor | is_staff

can_embargo = has_feature_level(1)

can_embargo_permananently = has_feature_level(2) | has_perm_embargo

can_view = can_edit | is_viewer | is_from_agency | is_proxy | ~is_private


@predicate
@skip_if_not_obj
@user_authenticated
def can_view_composer_child(user, composer):
    for foia in composer.foias.all():
        if foia.has_perm(user, "view"):
            return True
    return False


@predicate
@skip_if_not_obj
@user_authenticated
def is_owner_composer(user, composer):
    return composer.user_id == user.pk


can_view_composer = can_view_composer_child | is_owner_composer | is_staff

can_edit_composer = is_owner_composer | is_staff

add_perm("foia.change_foiarequest", can_edit)
add_perm("foia.view_foiarequest", can_view)
add_perm("foia.embargo_foiarequest", (can_edit | no_foia) & can_embargo)
add_perm(
    "foia.embargo_perm_foiarequest", (can_edit | no_foia) & can_embargo_permananently
)
add_perm(
    "foia.crowdfund_foiarequest",  # why cant editors crowdfund?
    (is_owner | is_staff) & ~has_crowdfund & has_status("payment"),
)
add_perm("foia.appeal_foiarequest", can_edit & is_appealable)
add_perm("foia.thank_foiarequest", can_edit & is_thankable)
add_perm("foia.flag_foiarequest", is_authenticated)
add_perm("foia.followup_foiarequest", can_edit)
add_perm("foia.agency_reply_foiarequest", is_from_agency)
add_perm("foia.upload_attachment_foiarequest", can_edit | is_from_agency)
add_perm("foia.pay_foiarequest", can_edit & is_payable)

add_perm("foia.view_foiacomposer", can_view_composer)
add_perm("foia.delete_foiacomposer", can_edit_composer & has_status("started"))
add_perm("foia.upload_attachment_foiacomposer", can_edit_composer)
add_perm("foia.change_foiacomposer", can_edit_composer)

add_perm("foia.view_rawemail", has_feature_level(1))
add_perm("foia.file_multirequest", has_feature_level(1))
add_perm("foia.export_csv", has_feature_level(1))
add_perm("foia.zip_download_foiarequest", can_edit)
add_perm("foia.set_info_foiarequest", is_authenticated)
add_perm("foia.unlimited_attachment_size", is_staff | is_agency_user)
