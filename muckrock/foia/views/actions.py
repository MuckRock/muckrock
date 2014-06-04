"""
FOIA views for actions
"""

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.template import RequestContext

from collections import namedtuple
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging
import stripe
import sys

from muckrock.accounts.forms import PaymentForm
from muckrock.crowdfund.forms import CrowdfundEnableForm
from muckrock.crowdfund.models import CrowdfundRequest
from muckrock.foia.forms import FOIADeleteForm, FOIAAdminFixForm, FOIANoteForm, \
                                FOIAEmbargoForm, FOIAEmbargoDateForm, FOIAFileFormSet
from muckrock.foia.models import FOIARequest, FOIAFile
from muckrock.foia.views.comms import save_foia_comm
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.settings import STRIPE_SECRET_KEY, STRIPE_PUB_KEY

logger = logging.getLogger(__name__)
stripe.api_key = STRIPE_SECRET_KEY

def _foia_action(request, jurisdiction, jidx, slug, idx, action):
    """Generic helper for FOIA actions"""
    # pylint: disable=R0913

    jmodel = get_object_or_404(Jurisdiction, slug=jurisdiction, pk=jidx)
    foia = get_object_or_404(FOIARequest, jurisdiction=jmodel, slug=slug, pk=idx)
    form_class = action.form_class(request, foia)

    if action.must_own and foia.user != request.user:
        messages.error(request, 'You may only %s your own requests' % action.msg)
        return redirect(foia)

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
    context.update({'form': form, 'foia': foia, 'heading': action.heading, 'action': action.value})
    return render_to_response(action.template, context,
                              context_instance=RequestContext(request))

Action = namedtuple('Action', 'form_actions msg tests form_class return_url '
                              'heading value must_own template extra_context')

@user_passes_test(lambda u: u.is_staff)
def admin_fix(request, jurisdiction, jidx, slug, idx):
    """Send an email from the requests auto email address"""

    jmodel = get_object_or_404(Jurisdiction, slug=jurisdiction, pk=jidx)
    foia = get_object_or_404(FOIARequest, jurisdiction=jmodel, slug=slug, pk=idx)

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
            save_foia_comm(request, foia, from_who, form.cleaned_data['comm'],
                            'Admin Fix submitted', formset, snail=form.cleaned_data['snail_mail'])
            return redirect(foia)
    else:
        form = FOIAAdminFixForm(instance=foia)
        formset = FOIAFileFormSet(queryset=FOIAFile.objects.none())

    context = {'form': form, 'foia': foia, 'heading': 'Email from Request Address',
               'formset': formset, 'action': 'Submit'}
    return render_to_response('foia/foiarequest_action.html', context,
                              context_instance=RequestContext(request))

@login_required
def note(request, jurisdiction, jidx, slug, idx):
    """Add a note to a request"""

    def form_actions(_, foia, form):
        """Save the FOI note"""
        foia_note = form.save(commit=False)
        foia_note.foia = foia
        foia_note.date = datetime.now()
        foia_note.save()

    action = Action(
        form_actions=form_actions,
        msg='add notes',
        tests=[],
        form_class=lambda r, f: FOIANoteForm,
        return_url=lambda r, f: f.get_absolute_url() + '#tabs-notes',
        heading='Add Note',
        value='Add',
        must_own=True,
        template='foia/foiarequest_action.html',
        extra_context=lambda f: {})
    return _foia_action(request, jurisdiction, jidx, slug, idx, action)

@login_required
def delete(request, jurisdiction, jidx, slug, idx):
    """Delete a non-submitted FOIA Request"""

    def form_actions(request, foia, _):
        """Delete the FOI request"""
        foia.delete()
        messages.info(request, 'Request succesfully deleted')

    action = Action(
        form_actions=form_actions,
        msg='delete',
        tests=[(lambda f: f.is_deletable(), 'You may only delete draft requests.')],
        form_class=lambda r, f: FOIADeleteForm,
        return_url=lambda r, f: reverse('foia-mylist', kwargs={'view': 'all'}),
        heading='Delete FOI Request',
        value='Delete',
        must_own=True,
        template='foia/foiarequest_action.html',
        extra_context=lambda f: {})
    return _foia_action(request, jurisdiction, jidx, slug, idx, action)

@login_required
def embargo(request, jurisdiction, jidx, slug, idx):
    """Change the embargo on a request"""

    def form_actions(_, foia, form):
        """Update the embargo date"""
        foia.embargo = form.cleaned_data.get('embargo')
        foia.date_embargo = form.cleaned_data.get('date_embargo')
        foia.save()
        logger.info('Embargo set by user for FOI Request %d %s to %s',
                    foia.pk, foia.title, foia.embargo)

    action = Action(
        form_actions=form_actions,
        msg='embargo',
        tests=[(lambda f: f.user.get_profile().can_embargo(),
                  'You may not embargo requests with your account type')],
        form_class=lambda r, f: FOIAEmbargoDateForm if f.date_embargo \
                                  else FOIAEmbargoForm,
        return_url=lambda r, f: f.get_absolute_url(),
        heading='Update the Embargo Date',
        value='Update',
        must_own=True,
        template='foia/foiarequest_action.html',
        extra_context=lambda f: {})
    return _foia_action(request, jurisdiction, jidx, slug, idx, action)

@login_required
def pay_request(request, jurisdiction, jidx, slug, idx):
    """Pay us through CC for the payment on a request"""
    # pylint: disable=W0142

    def form_actions(request, foia, form):
        """Pay for request"""
        try:
            amount = int(foia.price * 105)
            request.user.get_profile().pay(form, amount,
                                           'Charge for request: %s %s' % (foia.title, foia.pk))
            foia.status = 'processed'
            foia.save()

            send_mail('[PAYMENT] Freedom of Information Request: %s' % (foia.title),
                      render_to_string('foia/admin_payment.txt',
                                       {'request': foia, 'amount': amount / 100.0}),
                      'info@muckrock.com', ['requests@muckrock.com'], fail_silently=False)

            logger.info('%s has paid %0.2f for request %s',
                        request.user.username, amount/100, foia.title)
            messages.success(request, 'Your payment was successful')
            return HttpResponseRedirect(reverse('acct-my-profile'))
        except stripe.CardError as exc:
            messages.error(request, 'Payment error: %s' % exc)
            logger.error('Payment error: %s', exc, exc_info=sys.exc_info())
            return HttpResponseRedirect(reverse('foia-pay',
                kwargs={'jurisdiction': foia.jurisdiction.slug,
                        'slug': foia.slug,
                        'idx': foia.pk}))

    action = Action(
        form_actions=form_actions,
        msg='pay for',
        tests=[(lambda f: f.is_payable(),
                  'You may only pay for requests that require a payment')],
        form_class=lambda r, f: lambda *args, **kwargs: PaymentForm(request=r, *args, **kwargs),
        return_url=lambda r, f: f.get_absolute_url(),
        heading='Pay for Request',
        value='Pay',
        must_own=True,
        template='registration/cc.html',
        extra_context=lambda f: {'desc': 'You will be charged $%.2f for this request' %
                                   (f.price * Decimal('1.05')),
                                   'pub_key': STRIPE_PUB_KEY})
    return _foia_action(request, jurisdiction, jidx, slug, idx, action)

@login_required
def crowdfund_request(request, jurisdiction, jidx, slug, idx):
    """Enable crowdfunding on the request"""
    # pylint: disable=W0142

    def form_actions(request, foia, form):
        """Form actions"""
        # pylint: disable=unused-argument
        crowdfund = CrowdfundRequest.objects.create(foia=foia,
            payment_required=foia.price * Decimal('1.05'),
            date_due=date.today() + timedelta(30))
        messages.success(request, 'You have succesfully started a crowdfunding campaign')
        send_mail('%s has launched a crowdfunding campaign' % request.user.username,
                  render_to_string('crowdfund/notify.txt',
                                   {'crowdfund': crowdfund, 'user': request.user}),
                  'info@muckrock.com', ['requests@muckrock.com'], fail_silently=False)

    action = Action(
        form_actions=form_actions,
        msg='enabled crowdfunding for',
        tests=[(lambda f: f.is_payable(),
                  'You may only crowdfund requests that require a payment')],
        form_class=lambda r, f: CrowdfundEnableForm,
        return_url=lambda r, f: f.get_absolute_url(),
        heading='Enable Crowdfunding for Request',
        value='Crowdfund',
        must_own=True,
        template='foia/foiarequest_action.html',
        extra_context=lambda f: {'desc': 'By enabling crowdfunding, others will be able to '
                                           'contribute funds toward the money required to fufill '
                                           'this request'}
    )
    return _foia_action(request, jurisdiction, jidx, slug, idx, action)

@login_required
def follow(request, jurisdiction, jidx, slug, idx):
    """Follow or unfollow a request"""

    jmodel = get_object_or_404(Jurisdiction, slug=jurisdiction, pk=jidx)
    foia = get_object_or_404(FOIARequest, jurisdiction=jmodel, slug=slug, id=idx)

    if foia.user == request.user:
        messages.error(request, 'You may not follow your own request')
    else:
        if foia.followed_by.filter(user=request.user):
            foia.followed_by.remove(request.user.get_profile())
            messages.info(request, 'You are no longer following %s' % foia.title)
        else:
            foia.followed_by.add(request.user.get_profile())
            messages.info(request, 'You are now following %s.  You will be notified whenever it '
                                   'is updated.' % foia.title)

    return redirect(foia)
