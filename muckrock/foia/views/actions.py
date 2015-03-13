"""
FOIA views for actions
"""

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.template import RequestContext

from collections import namedtuple
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging
import stripe
import sys

from muckrock.crowdfund.forms import CrowdfundEnableForm
from muckrock.crowdfund.models import CrowdfundRequest
from muckrock.foia.forms import \
    FOIADeleteForm, \
    FOIAAdminFixForm, \
    FOIANoteForm, \
    FOIAEmbargoForm, \
    FOIAFileFormSet
from muckrock.foia.models import FOIARequest, FOIAFile
from muckrock.foia.views.comms import save_foia_comm
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.settings import STRIPE_SECRET_KEY

logger = logging.getLogger(__name__)
stripe.api_key = STRIPE_SECRET_KEY

RequestAction = namedtuple(
    'RequestAction',
    'form_actions msg tests form_class return_url heading value must_own template extra_context'
)

action_template = 'forms/base_form.html'

# Helper Functions

def _get_foia(jurisdiction, jidx, slug, idx):
    """Returns a foia object"""
    jmodel = get_object_or_404(Jurisdiction, slug=jurisdiction, pk=jidx)
    foia = get_object_or_404(FOIARequest, jurisdiction=jmodel, slug=slug, id=idx)
    return foia

def _foia_action(request, foia, action):
    """Generic helper for FOIA actions"""
    form_class = action.form_class(request, foia)
    # Check that the request belongs to the user
    if action.must_own and not foia.editable_by(request.user) and not request.user.is_staff:
        msg = 'You may only %s your own requests.' % action.msg
        messages.error(request, msg)
        return redirect(foia)
    # Check that the action is valid
    for test, msg in action.tests:
        if not test(foia):
            messages.error(request, msg)
            return redirect(foia)

    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            action.form_actions(request, foia, form)
            return HttpResponseRedirect(action.return_url(request, foia))
    else:
        if isinstance(form_class, type) and issubclass(form_class, forms.ModelForm):
            form = form_class(instance=foia)
        else:
            form = form_class()

    context = action.extra_context(foia)
    args = {
        'form': form,
        'foia': foia,
        'heading': action.heading,
        'action': action.value
    }
    context.update(args)
    return render_to_response(
        action.template,
        context,
        context_instance=RequestContext(request)
    )

# User Actions

@login_required
def note(request, jurisdiction, jidx, slug, idx):
    """Add a note to a request"""
    def form_actions(_, foia, form):
        """Helper class, passed to generic function"""
        foia_note = form.save(commit=False)
        foia_note.foia = foia
        foia_note.date = datetime.now()
        foia_note.save()
    foia = _get_foia(jurisdiction, jidx, slug, idx)
    action = RequestAction(
        form_actions=form_actions,
        msg='add notes',
        tests=[],
        form_class=lambda r, f: FOIANoteForm,
        return_url=lambda r, f: f.get_absolute_url() + '#tabs-notes',
        heading='Add Note',
        value='Add',
        must_own=True,
        template=action_template,
        extra_context=lambda f: {}
    )
    return _foia_action(request, foia, action)

@login_required
def delete(request, jurisdiction, jidx, slug, idx):
    """Delete a non-submitted FOIA Request"""
    def form_actions(request, foia, _):
        """Helper class, passed to generic function"""
        foia.delete()
        messages.success(request, 'The draft has been deleted.')
    foia = _get_foia(jurisdiction, jidx, slug, idx)
    action = RequestAction(
        form_actions=form_actions,
        msg='delete',
        tests=[(
            lambda f: f.is_deletable(),
            'You can only delete drafts.'
        )],
        form_class=lambda r, f: FOIADeleteForm,
        return_url=lambda r, f: reverse('foia-mylist'),
        heading='Delete FOI Request',
        value='Delete',
        must_own=True,
        template=action_template,
        extra_context=lambda f: {}
    )
    return _foia_action(request, foia, action)

@login_required
def permanent_embargo(request, jurisdiction, jidx, slug, idx):
    """Toggle the permanant embargo on the FOIA Request"""
    foia = _get_foia(jurisdiction, jidx, slug, idx)
    is_org_member = request.user == foia.user and request.user.get_profile().organization != None
    if foia.editable_by(request.user) and is_org_member or request.user.is_staff:
        if foia.embargo == True:
            if foia.is_permanently_embargoed():
                foia.permanent_embargo = False
                msg = 'The permanent embargo on this request has been lifted.'
            else:
                foia.permanent_embargo = True
                msg = 'The request is now permanently embargoed.'
            messages.success(request, msg)
            foia.save()
        else:
            messages.error(request, 'You may only permanently embargo requests that '
                                    'already have an embargo.')
    else:
        messages.error(request, 'Only staff and org members may permanently embargo '
                                'their requests.')
    return redirect(foia)

@login_required
def embargo(request, jurisdiction, jidx, slug, idx):
    """Change the embargo on a request"""
    def form_actions(_, foia, form):
        """Update the embargo date"""
        foia.embargo = True
        foia.date_embargo = form.cleaned_data.get('date_embargo')
        foia.permanent_embargo = False
        foia.save()
        logger.info(
            'Embargo set by user for FOI Request %d %s to %s',
            foia.pk,
            foia.title,
            foia.embargo
        )
    foia = _get_foia(jurisdiction, jidx, slug, idx)
    finished_status = ['rejected', 'no_docs', 'done', 'partial', 'abandoned']
    if foia.embargo or foia.status not in finished_status:
        foia.embargo = not foia.embargo
        foia.permanent_embargo = False
        foia.save()
        return redirect(foia)
    else:
        action = RequestAction(
            form_actions=form_actions,
            msg='embargo',
            tests=[(
                lambda f: f.user.get_profile().can_embargo(),
                'You may not embargo requests with your account type'
            )],
            form_class=lambda r, f: FOIAEmbargoForm,
            return_url=lambda r, f: f.get_absolute_url(),
            heading='Update the Embargo Date',
            value='Update',
            must_own=True,
            template='forms/foia/embargo.html',
            extra_context=lambda f: {}
        )
        return _foia_action(request, foia, action)

@login_required
def pay_request(request, jurisdiction, jidx, slug, idx):
    """Pay us through CC for the payment on a request"""
    foia = _get_foia(jurisdiction, jidx, slug, idx)
    token = request.POST.get('stripe_token', False)
    email = request.POST.get('stripe_email', False)
    amount = request.POST.get('amount', False)
    if token and email and amount:
        try:
            request.user.get_profile().pay(
                token,
                amount,
                'Charge for request: %s %s' % (foia.title, foia.pk)
            )
        except stripe.CardError as exc:
            messages.error(request, 'Payment error: %s' % exc)
            logger.error('Payment error: %s', exc, exc_info=sys.exc_info())
            return redirect(foia)
        msg = 'Your payment was successful. We will get this to the agency right away.'
        messages.success(request, msg)
        logger.info(
            '%s has paid %0.2f for request %s',
            request.user.username,
            int(amount)/100,
            foia.title
        )
        foia.status = 'processed'
        foia.save()
        args = {'request': foia, 'amount': int(amount) / 100.0}
        send_mail(
            '[PAYMENT] Freedom of Information Request: %s' % (foia.title),
            render_to_string('text/foia/admin_payment.txt', args),
            'info@muckrock.com',
            ['requests@muckrock.com'],
            fail_silently=False
        )
    return redirect(foia)

@login_required
def follow(request, jurisdiction, jidx, slug, idx):
    """Follow or unfollow a request"""
    foia = _get_foia(jurisdiction, jidx, slug, idx)
    if foia.user != request.user:
        followers = foia.followed_by
        if followers.filter(user=request.user): # If following, unfollow
            followers.remove(request.user.get_profile())
            msg = 'You are no longer following %s' % foia.title
        else: # If not following, follow
            followers.add(request.user.get_profile())
            msg = ('You are now following %s. '
                   'We will notify you when it is updated.') % foia.title
        messages.success(request, msg)
    else:
        messages.error(request, 'You may not follow your own request.')
    return redirect(foia)

@login_required
def toggle_autofollowups(request, jurisdiction, jidx, slug, idx):
    """Toggle autofollowups"""
    foia = _get_foia(jurisdiction, jidx, slug, idx)

    if foia.editable_by(request.user):
        foia.disable_autofollowups = not foia.disable_autofollowups
        foia.save()
        action = 'disabled' if foia.disable_autofollowups else 'enabled'
        msg = 'Autofollowups have been %s' % action
        messages.success(request, msg)
    else:
        msg = 'You must own the request to toggle auto-followups.'
        messages.error(request, msg)
    return redirect(foia)

# Staff Actions
@user_passes_test(lambda u: u.is_staff)
def admin_fix(request, jurisdiction, jidx, slug, idx):
    """Send an email from the requests auto email address"""
    foia = _get_foia(jurisdiction, jidx, slug, idx)

    if request.method == 'POST':
        form = FOIAAdminFixForm(request.POST)
        formset = FOIAFileFormSet(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            if form.cleaned_data['email']:
                foia.email = form.cleaned_data['email']
            if form.cleaned_data['other_emails']:
                foia.other_emails = form.cleaned_data['other_emails']
            if form.cleaned_data['from_email']:
                from_who = form.cleaned_data['from_email']
            else:
                from_who = foia.user.get_full_name()
            save_foia_comm(
                request,
                foia,
                from_who,
                form.cleaned_data['comm'],
                'Admin Fix submitted',
                formset,
                snail=form.cleaned_data['snail_mail']
            )
            return redirect(foia)
        else:
            messages.error(request, 'Could not apply admin fix.')
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
def crowdfund_request(request, jurisdiction, jidx, slug, idx):
    """Crowdfund a request"""
    foia = FOIARequest.objects.get(pk=idx)
    owner_or_staff = request.user == foia.user or request.user.is_staff

    if not owner_or_staff:
        messages.error(request, 'You can only crowdfund your own requests.')
        return redirect(foia)
    if foia.has_crowdfund():
        messages.error(request, 'You can only run one crowdfund per requests.')
        return redirect(foia)

    context = {}

    return render_to_response(
        'forms/foia/crowdfund.html',
        context,
        context_instance=RequestContext(request)
    )
