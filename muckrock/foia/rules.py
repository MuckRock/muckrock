"""Rules based permissions for the FOIA app"""

# needed for rules
from __future__ import absolute_import

from datetime import date
from rules import (
        add_perm,
        is_authenticated,
        is_staff,
        predicate,
        )

from muckrock.foia.models.request import END_STATUS

# pylint: disable=missing-docstring
# pylint: disable=unused-argument

def has_status(*statuses):
    @predicate('has_status:%s' % ','.join(statuses))
    def inner(user, foia):
        return foia.status in statuses
    return inner

@predicate
def is_owner(user, foia):
    return foia.user == user

@predicate
def is_editor(user, foia):
    return foia.edit_collaborators.filter(pk=user.pk).exists()

can_edit = is_owner | is_editor | is_staff

@predicate
def is_viewer(user, foia):
    return foia.read_collaborators.filter(pk=user.pk).exists()

@predicate
def is_embargoed(user, foia):
    return foia.embargo

is_private = has_status('started') | is_embargoed

is_editable = has_status('started')

is_deletable = has_status('started')

@predicate
def has_thanks(user, foia):
    return foia.communications.filter(thanks=True).exists()

is_thankable = ~has_thanks & has_status(*END_STATUS)

@predicate
def has_appealable_jurisdiction(user, foia):
    return foia.agency and foia.agency.jurisdiction.can_appeal()

@predicate
def is_overdue(user, foia):
    return foia.date_due is not None and foia.date_due < date.today()

is_appealable = has_appealable_jurisdiction & (
        (has_status('processed', 'appealing') & is_overdue) |
        ~has_status('processed', 'appealing', 'started', 'submitted'))

@predicate
def has_crowdfund(user, foia):
    return bool(foia.crowdfund)

# User predicates

@predicate
def is_advanced_type(user):
    return (user.profile and
            user.profile.acct_type in ['admin', 'beta', 'pro', 'proxy'])

@predicate
def is_admin(user):
    return user.profile.acct_type == 'admin'

@predicate
def is_org_member(user):
    return (user.profile and user.profile.organization and
            user.profile.organization.active)

is_advanced = is_advanced_type | is_org_member

can_embargo = is_advanced

can_embargo_permananently = is_admin | is_org_member

add_perm('foia.change_foiarequest', can_edit)
add_perm('foia.delete_foiarequest', can_edit & is_deletable)
add_perm('foia.view_foiarequest', can_edit | is_viewer | ~is_private)
add_perm('foia.embargo_foiarequest', can_edit & can_embargo)
add_perm('foia.embargo_perm_foiarequest', can_edit & can_embargo_permananently)
add_perm('foia.crowdfund_foiarequest', # why cant editors crowdfund?
        (is_owner | is_staff) & ~has_crowdfund & has_status('payment'))
add_perm('foia.appeal_foiarequest', can_edit & is_appealable)
add_perm('foia.thank_foiarequest', can_edit & is_thankable)
add_perm('foia.flag_foiarequest', is_authenticated) # Why must be authenticated for flag?
add_perm('foia.followup_foiarequest', can_edit & ~has_status('started'))
add_perm('foia.view_rawemail', is_advanced)
add_perm('foia.file_multirequest', is_advanced)

