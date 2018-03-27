"""Rules based permissions for the FOIA app"""

# pylint: disable=missing-docstring
# pylint: disable=unused-argument

# needed for rules
from __future__ import absolute_import

# Standard Library
import inspect
from datetime import date
from functools import wraps

# Third Party
from rules import add_perm, is_authenticated, is_staff, predicate

# MuckRock
from muckrock.foia.models.request import END_STATUS


def skip_if_not_foia(func):
    """Decorator for predicates
    Skip the predicate if foia is None"""

    @wraps(func)
    def inner(user, foia):
        if foia is None:
            return None
        else:
            return func(user, foia)

    return inner


def user_authenticated(func):
    """Decorator for predicates
    Return false if user is not authenticated"""
    argspec = inspect.getargspec(func)
    if len(argspec.args) == 2:

        @wraps(func)
        def inner(user, foia):
            return user.is_authenticated() and func(user, foia)
    elif len(argspec.args) == 1:

        @wraps(func)
        def inner(user):
            return user.is_authenticated() and func(user)

    return inner


def has_status(*statuses):
    @predicate('has_status:%s' % ','.join(statuses))
    @skip_if_not_foia
    def inner(user, foia):
        return foia.status in statuses

    return inner


@predicate
@skip_if_not_foia
def is_owner(user, foia):
    return foia.user == user


@predicate
def no_foia(user, foia):
    return foia is None


@predicate
@skip_if_not_foia
def is_editor(user, foia):
    return (
        user.is_authenticated()
        and foia.edit_collaborators.filter(pk=user.pk).exists()
    )


@predicate
@skip_if_not_foia
def is_read_collaborator(user, foia):
    return (
        user.is_authenticated()
        and foia.read_collaborators.filter(pk=user.pk).exists()
    )


@predicate
@skip_if_not_foia
@user_authenticated
def is_org_shared(user, foia):
    return (
        foia.user.is_authenticated() and foia.user.profile.org_share
        and foia.user.profile.organization is not None
        and foia.user.profile.organization == user.profile.organization
    )


is_viewer = is_read_collaborator | is_org_shared


@predicate
@skip_if_not_foia
def is_embargoed(user, foia):
    return foia.embargo


is_private = has_status('started') | is_embargoed

is_editable = has_status('started')

is_deletable = has_status('started')


@predicate
@skip_if_not_foia
def has_thanks(user, foia):
    return foia.communications.filter(thanks=True).exists()


is_thankable = ~has_thanks & has_status(*END_STATUS)


@predicate
@skip_if_not_foia
def has_appealable_jurisdiction(user, foia):
    return foia.agency and foia.agency.jurisdiction.has_appeal


@predicate
@skip_if_not_foia
def is_overdue(user, foia):
    return foia.date_due is not None and foia.date_due < date.today()


is_appealable = has_appealable_jurisdiction & (
    (has_status('processed', 'appealing') & is_overdue)
    | ~has_status('processed', 'appealing', 'started', 'submitted')
)


@predicate
@skip_if_not_foia
def has_crowdfund(user, foia):
    return bool(foia.crowdfund)


@predicate
@skip_if_not_foia
@user_authenticated
def match_agency(user, foia):
    return bool(user.profile.agency and user.profile.agency == foia.agency)


# User predicates


@predicate
@user_authenticated
def is_advanced_type(user):
    return user.profile.acct_type in ['admin', 'beta', 'pro', 'proxy']


@predicate
@user_authenticated
def is_admin(user):
    return user.profile.acct_type == 'admin'


@predicate
@user_authenticated
def is_agency_user(user):
    return user.profile.acct_type == 'agency'


@predicate
@user_authenticated
def is_org_member(user):
    return user.profile.organization and user.profile.organization.active


is_from_agency = is_agency_user & match_agency & ~has_status('started')

can_edit = is_owner | is_editor | is_staff

is_advanced = is_advanced_type | is_org_member

can_embargo = is_advanced

can_embargo_permananently = is_admin | is_org_member

can_view = can_edit | is_viewer | is_from_agency | ~is_private


@predicate
@user_authenticated
def can_view_composer_child(user, composer):
    for foia in composer.foias.all():
        if foia.has_perm(user, 'view'):
            return True
    return False


@predicate
@user_authenticated
def is_owner_composer(user, composer):
    if composer.user_id == user.pk:
        return True


can_view_composer = can_view_composer_child | is_owner_composer | is_staff

can_edit_composer = is_owner_composer | is_staff

add_perm('foia.change_foiarequest', can_edit)
add_perm('foia.delete_foiarequest', can_edit & is_deletable)
add_perm('foia.view_foiarequest', can_view)
add_perm('foia.embargo_foiarequest', (can_edit | no_foia) & can_embargo)
add_perm(
    'foia.embargo_perm_foiarequest',
    (can_edit | no_foia) & can_embargo_permananently
)
add_perm(
    'foia.crowdfund_foiarequest',  # why cant editors crowdfund?
    (is_owner | is_staff) & ~has_crowdfund & has_status('payment')
)
add_perm('foia.appeal_foiarequest', can_edit & is_appealable)
add_perm('foia.thank_foiarequest', can_edit & is_thankable)
add_perm('foia.flag_foiarequest', is_authenticated)
add_perm('foia.followup_foiarequest', can_edit & ~has_status('started'))
add_perm('foia.agency_reply_foiarequest', is_from_agency)
add_perm('foia.upload_attachment_foiarequest', can_edit | is_from_agency)

add_perm('foia.view_foiacomposer', can_view_composer)
add_perm('foia.upload_attachment_foiacomposer', can_edit_composer)

add_perm('foia.view_rawemail', is_advanced)
add_perm('foia.file_multirequest', is_advanced)
add_perm('foia.export_csv', is_advanced)
add_perm('foia.zip_download', can_edit)
