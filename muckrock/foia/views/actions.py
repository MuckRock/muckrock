"""
FOIA views for actions
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.shortcuts import (
        render_to_response,
        get_object_or_404,
        redirect,
        render,
        )
from django.template import RequestContext

import actstream
from datetime import datetime, timedelta
import logging
import stripe
import sys

from muckrock.crowdfund.forms import CrowdfundForm
from muckrock.foia.forms import (
    FOIADeleteForm,
    FOIAAdminFixForm,
    FOIAAgencyReplyForm,
    FOIAEmbargoForm,
    FOIAFileFormSet,
    )
from muckrock.foia.models import FOIARequest, FOIAFile, END_STATUS
from muckrock.jurisdiction.models import Jurisdiction

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
    if not request.user.has_perm('foia.delete_foiarequest', foia):
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
            if request.user.has_perm('foia.embargo_perm_foiarequest', foia):
                foia.permanent_embargo = permanent
            if expiration and foia.status in END_STATUS:
                foia.date_embargo = expiration
            foia.save(comment='updated embargo')
        return

    def create_embargo(request, foia):
        """Apply an embargo to the FOIA"""
        if request.user.has_perm('foia.embargo_foiarequest', foia):
            foia.embargo = True
            foia.save(comment='added embargo')
            logger.info('%s embargoed %s', request.user, foia)
            # unsubscribe all followers of the request
            # https://github.com/MuckRock/muckrock/issues/720
            followers = actstream.models.followers(foia)
            for follower in followers:
                actstream.actions.unfollow(follower, foia)
            actstream.action.send(request.user, verb='embargoed', action_object=foia)
            fine_tune_embargo(request, foia)
        else:
            logger.error('%s was forbidden from embargoing %s', request.user, foia)
            messages.error(request, 'You cannot embargo requests.')
        return

    def update_embargo(request, foia):
        """Update an embargo to the FOIA"""
        if request.user.has_perm('foia.embargo_foiarequest', foia):
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
        actstream.action.send(request.user, verb='unembargoed', action_object=foia)
        return

    foia = _get_foia(jurisdiction, jidx, slug, idx)
    has_perm = request.user.has_perm('foia.change_foiarequest', foia)
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

    if request.user.has_perm('foia.change_foiarequest', foia):
        foia.disable_autofollowups = not foia.disable_autofollowups
        foia.save(comment='toggled autofollowups')
        action = 'disabled' if foia.disable_autofollowups else 'enabled'
        msg = 'Autofollowups have been %s' % action
        messages.success(request, msg)
    else:
        msg = 'You must own the request to toggle auto-followups.'
        messages.error(request, msg)
    return redirect(foia)

# XXX move perm check inside, change this whole view to be part of detail
# Redo all of this
@user_passes_test(lambda u: u.has_perm('foia.agency_reply', foia))
def agency_reply(request, jurisdiction, jidx, slug, idx):
    """Allow agency users to reply directly"""
    foia = _get_foia(jurisdiction, jidx, slug, idx)
    # XXX check status

    if request.method == 'POST':
        form = FOIAAgencyReplyForm(request.POST, instance=foia)
        formset = FOIAFileFormSet(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            foia = form.save()
            # XXX mark foia as updated / email notify someone?
            foia.create_in_communication(
                    from_user=request.user,
                    text=form.cleaned_data['comm'],
                    formset=formset,
                    )
            messages.success(request, 'Reply succesfully submitted')
            return redirect(foia)
    else:
        form = FOIAAgencyReplyForm(instance=foia)
        formset = FOIAFileFormSet(queryset=FOIAFile.objects.none())
    context = {
        'form': form,
        'foia': foia,
        'formset': formset,
        'action': 'Submit'
    }
    return render_to_response(
        'forms/foia/admin_fix.html',
        context,
        context_instance=RequestContext(request)
    )


# Staff Actions
@user_passes_test(lambda u: u.is_staff)
def admin_fix(request, jurisdiction, jidx, slug, idx):
    """Send an email from the requests auto email address"""
    # XXX test this with comm users
    foia = _get_foia(jurisdiction, jidx, slug, idx)

    if request.method == 'POST':
        form = FOIAAdminFixForm(request.POST)
        formset = FOIAFileFormSet(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            if form.cleaned_data['email']:
                foia.contact = User.agency_objects.get_or_create_agency_user(
                        form.cleaned_data['email'],
                        agency=foia.agency)
            if form.cleaned_data['other_emails']:
                foia.cc_contacts.clear()
                for email in form.cleaned_data['other_emails'].split(','):
                    user = User.agency_objects.get_or_create_agency_user(
                            email,
                            agency=foia.agency)
                    foia.cc_contacts.add(user)
            if form.cleaned_data['from_email']:
                from_user = User.agency_objects.get_or_create_agency_user(
                        form.cleaned_data['from_email'])
            else:
                from_user = foia.user
            foia.create_out_communication(
                    from_user=from_user,
                    text=form.cleaned_data['comm'],
                    formset=formset,
                    )
            foia.submit(snail=form.cleaned_data['snail_mail'])
            messages.success(request, 'Admin Fix submitted')
            return redirect(foia)
    else:
        form = FOIAAdminFixForm(instance=foia)
        formset = FOIAFileFormSet(queryset=FOIAFile.objects.none())
    context = {
        'form': form,
        'foia': foia,
        'heading': 'Email from Request Address',
        'formset': formset,
        'action': 'Submit'
    }
    return render_to_response(
        'forms/foia/admin_fix.html',
        context,
        context_instance=RequestContext(request)
    )

@login_required
def crowdfund_request(request, idx, **kwargs):
    """Crowdfund a request"""
    # pylint: disable=unused-argument
    foia = FOIARequest.objects.get(pk=idx)
    # check for unauthorized access
    if not request.user.has_perm('foia.crowdfund_foiarequest', foia):
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
            actstream.action.send(
                request.user,
                verb='started',
                action_object=crowdfund,
                target=foia
            )
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

    return render_to_response(
        'forms/foia/crowdfund.html',
        {'form': form},
        context_instance=RequestContext(request)
    )
