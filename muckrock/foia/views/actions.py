"""
FOIA views for actions
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import (
        get_object_or_404,
        redirect,
        render,
        )

import actstream
from datetime import datetime, timedelta
import logging
import stripe
import sys

from muckrock.accounts.utils import validate_stripe_email
from muckrock.crowdfund.forms import CrowdfundForm
from muckrock.foia.forms import (
        FOIADeleteForm,
        FOIAEmbargoForm,
        )
from muckrock.foia.models import FOIARequest, END_STATUS
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.utils import new_action

logger = logging.getLogger(__name__)

# Helper Functions

def _get_foia(jurisdiction, jidx, slug, idx):
    """Returns a foia object"""
    jmodel = get_object_or_404(Jurisdiction, slug=jurisdiction, pk=jidx)
    foia = get_object_or_404(FOIARequest, jurisdiction=jmodel, slug=slug, id=idx)
    return foia

# remove this view?
@login_required
def delete(request, jurisdiction, jidx, slug, idx):
    """Delete a non-submitted FOIA Request"""
    foia = _get_foia(jurisdiction, jidx, slug, idx)
    if not foia.has_perm(request.user, 'delete'):
        messages.error(request, 'You may only delete your own drafts.')
        return redirect(foia)

    if request.method == 'POST':
        form = FOIADeleteForm(request.POST)
        if form.is_valid():
            foia.delete()
            messages.success(request, 'The draft has been deleted.')
            return redirect('foia-mylist')
    else:
        form = FOIADeleteForm()

    return render(request, 'forms/base_form.html', {'form': form})

# remove this view?
@login_required
def embargo(request, jurisdiction, jidx, slug, idx):
    """Change the embargo on a request"""

    def fine_tune_embargo(request, foia):
        """Adds an expiration date or makes permanent if necessary."""
        permanent = request.POST.get('permanent_embargo')
        expiration = request.POST.get('date_embargo')
        form = FOIAEmbargoForm({
            'permanent_embargo': request.POST.get('permanent_embargo'),
            'date_embargo': request.POST.get('date_embargo')
        })
        if form.is_valid():
            permanent = form.cleaned_data['permanent_embargo']
            expiration = form.cleaned_data['date_embargo']
            if foia.has_perm(request.user, 'embargo_perm'):
                foia.permanent_embargo = permanent
            if expiration and foia.status in END_STATUS:
                foia.date_embargo = expiration
            foia.save(comment='updated embargo')
        return

    def create_embargo(request, foia):
        """Apply an embargo to the FOIA"""
        if foia.has_perm(request.user, 'embargo'):
            foia.embargo = True
            foia.save(comment='added embargo')
            logger.info('%s embargoed %s', request.user, foia)
            new_action(request.user, 'embargoed', target=foia)
            fine_tune_embargo(request, foia)
        else:
            logger.error('%s was forbidden from embargoing %s', request.user, foia)
            messages.error(request, 'You cannot embargo requests.')
        return

    def update_embargo(request, foia):
        """Update an embargo to the FOIA"""
        if foia.has_perm(request.user, 'embargo'):
            fine_tune_embargo(request, foia)
        else:
            logger.error('%s was forbidden from updating the embargo on %s', request.user, foia)
            messages.error(request, 'You cannot update this embargo.')
        return

    def delete_embargo(request, foia):
        """Remove an embargo from the FOIA"""
        foia.embargo = False
        foia.save(comment='removed embargo')
        logger.info('%s unembargoed %s', request.user, foia)
        new_action(request.user, 'unembargoed', target=foia)
        return

    foia = _get_foia(jurisdiction, jidx, slug, idx)
    has_perm = foia.has_perm(request.user, 'change')
    if request.method == 'POST' and has_perm:
        embargo_action = request.POST.get('embargo')
        if embargo_action == 'create':
            create_embargo(request, foia)
        elif embargo_action == 'update':
            update_embargo(request, foia)
        elif embargo_action == 'delete':
            delete_embargo(request, foia)
    return redirect(foia)

@login_required
def pay_request(request, jurisdiction, jidx, slug, idx):
    """Pay us through CC for the payment on a request"""
    foia = _get_foia(jurisdiction, jidx, slug, idx)
    token = request.POST.get('stripe_token')
    email = request.POST.get('stripe_email')
    email = validate_stripe_email(email)
    amount = request.POST.get('stripe_amount')
    if request.method == 'POST':
        error_msg = None
        if not token:
            error_msg = 'Missing Stripe token.'
        if not email:
            error_msg = 'Missing email address.'
        if not amount:
            error_msg = 'Missing payment amount.'
        if error_msg is not None:
            messages.error(request, 'Payment error: %s' % error_msg)
            logger.warning('Payment error: %s', error_msg, exc_info=sys.exc_info())
            return redirect(foia)
        try:
            metadata = {
                'email': email,
                'action': 'request-fee',
                'foia': foia.pk
            }
            amount = int(amount)
            request.user.profile.pay(token, amount, metadata)
            foia.pay(request.user, amount / 100.0)
        except (stripe.InvalidRequestError, stripe.CardError, ValueError) as exception:
            messages.error(request, 'Payment error: %s' % exception)
            logger.warning('Payment error: %s', exception, exc_info=sys.exc_info())
            return redirect(foia)
        msg = 'Your payment was successful. We will get this to the agency right away!'
        messages.success(request, msg)
    return redirect(foia)

@login_required
def follow(request, jurisdiction, jidx, slug, idx):
    """Follow or unfollow a request"""
    foia = _get_foia(jurisdiction, jidx, slug, idx)
    if actstream.actions.is_following(request.user, foia):
        actstream.actions.unfollow(request.user, foia)
        messages.success(request, 'You are no longer following this request.')
    else:
        actstream.actions.follow(request.user, foia, actor_only=False)
        messages.success(request, 'You are now following this request.')
    return redirect(foia)

@login_required
def toggle_autofollowups(request, jurisdiction, jidx, slug, idx):
    """Toggle autofollowups"""
    foia = _get_foia(jurisdiction, jidx, slug, idx)

    if foia.has_perm(request.user, 'change'):
        foia.disable_autofollowups = not foia.disable_autofollowups
        foia.save(comment='toggled autofollowups')
        action = 'disabled' if foia.disable_autofollowups else 'enabled'
        msg = 'Autofollowups have been %s' % action
        messages.success(request, msg)
    else:
        msg = 'You must own the request to toggle auto-followups.'
        messages.error(request, msg)
    return redirect(foia)

# Staff Actions
@transaction.atomic
@login_required
def crowdfund_request(request, idx, **kwargs):
    """Crowdfund a request"""
    # pylint: disable=unused-argument
    # select for update locks this request in order to prevent a race condition
    # allowing multiple crowdfunds to be created for it
    foia = FOIARequest.objects.select_for_update().get(pk=idx)
    # check for unauthorized access
    if not foia.has_perm(request.user, 'crowdfund'):
        messages.error(request, 'You may not crowdfund this request.')
        return redirect(foia)
    if request.method == 'POST':
        # save crowdfund object
        form = CrowdfundForm(request.POST)
        if form.is_valid():
            crowdfund = form.save()
            foia.crowdfund = crowdfund
            foia.save(comment='added a crowdfund')
            messages.success(request, 'Your crowdfund has started, spread the word!')
            new_action(
                request.user,
                'began crowdfunding',
                action_object=crowdfund,
                target=foia)
            crowdfund.send_intro_email(request.user)
            return redirect(foia)

    elif request.method == 'GET':
        # create crowdfund form
        default_crowdfund_duration = 30
        date_due = datetime.now() + timedelta(default_crowdfund_duration)
        initial = {
            'name': u'Crowdfund Request: %s' % unicode(foia),
            'description': 'Help cover the request fees needed to free these docs!',
            'payment_required': foia.get_stripe_amount(),
            'date_due': date_due,
            'foia': foia
        }
        form = CrowdfundForm(initial=initial)

    return render(
            request,
            'forms/foia/crowdfund.html',
            {'form': form},
            )
