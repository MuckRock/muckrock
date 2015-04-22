"""
Views for the crowdfund application
"""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.views.generic.detail import DetailView

import ast
from decimal import Decimal
import logging
import stripe
import sys

from muckrock.crowdfund.forms import CrowdfundRequestPaymentForm
from muckrock.crowdfund.models import \
    CrowdfundRequest, \
    CrowdfundProject, \
    CrowdfundRequestPayment, \
    CrowdfundProjectPayment
from muckrock.settings import STRIPE_SECRET_KEY, STRIPE_PUB_KEY

logger = logging.getLogger(__name__)
stripe.api_key = STRIPE_SECRET_KEY

def process_payment(amount, email, token):
    # double -> int conversion
    # http://stackoverflow.com/a/13528445/4256689
    amount = int(amount) * 100
    logging.debug(amount)
    try:
        stripe.Charge.create(
            amount=amount,
            source=token,
            currency='usd',
            description='Crowdfund contribution',
            receipt_email=email
        )
        return True
    except (stripe.card_error, stripe.api_error) as exception:
        logging.error('Processing a Stripe charge: %s' % exception)
        messages.error(request, ('We encountered an error processing your card.'
                                ' Your card has not been charged.'))
        return False

class CrowdfundRequestDetail(DetailView):
    """
    Presents details about a crowdfunding campaign,
    as well as providing a private endpoint for contributions
    """
    model = CrowdfundRequest
    template_name = 'details/crowdfund_request_detail.html'

    def get_context_data(self, **kwargs):
        """Adds Stripe public key to context"""
        context = super(CrowdfundRequestDetail, self).get_context_data(**kwargs)
        context['stripe_pk'] = STRIPE_PUB_KEY
        return context

    def post(self, request, **kwargs):
        """
        First we validate the payment form, so we don't charge someone's card by accident.
        Next, we charge their card. Finally, use the validated payment form to create and
        return a CrowdfundRequestPayment object.
        """
        amount = request.POST.get('amount')
        show = request.POST.get('show')
        crowdfund = request.POST.get('crowdfund')
        email = request.POST.get('email')
        token = request.POST.get('token')
        if request.user.is_authenticated() and show:
            user = request.user
        else:
            user = None
        logging.debug(user)
        redirect_url = request.POST.get('redirect')
        crowdfund_object = get_object_or_404(CrowdfundRequest, pk=crowdfund)

        logging.info('-- Crowdfund Payment --')
        logging.info('Amount: %s' % amount)
        logging.info('Show: %s' % show)
        logging.info('Crowdfund: %s' % crowdfund)
        logging.info('Email: %s' % email)
        logging.info('Token: %s' % token)
        logging.info('User: %s' % user)

        amount = Decimal(float(amount)/100)
        payment_data = {'amount': amount, 'show': show, 'crowdfund': crowdfund}
        payment_form = CrowdfundRequestPaymentForm(payment_data)
        payment_object = None
        if payment_form.is_valid() and email and token:
            if process_payment(amount, email, token):
                payment_object = payment_form.save(commit=False)
                payment_object.user = user
                payment_object.save()
                crowdfund_object.update_payment_received()
        # if AJAX, return the payment
        # else, return to the crowdfund page
        if request.is_ajax():
            return HttpResponse(200)
        else:
            return redirect(crowdfund_object.foia)

def _contribute(request, crowdfund, payment_model, redirect_url):
    """Contribute to a crowdfunding request or project"""
    amount = request.POST.get('amount', False)
    token = request.POST.get('stripe_token', False)
    desc = 'Contribute to Crowdfunding: %s %s' % (crowdfund, crowdfund.pk)
    if amount and token:
        try:
            amount = int(amount) # normalizes amount for Stripe
            if request.user.is_authenticated():
                user = request.user
                user.get_profile().pay(token, amount, desc)
                name = user.username
            else:
                desc = '%s: %s' % (request.POST.get('stripe_email'), desc)
                stripe.Charge.create(
                    amount=amount,
                    description=desc,
                    currency='usd',
                    card=token
                )
                user = None
                name = 'A visitor'
            amount = float(amount)/100
            payment_model.objects.create(
                user=user,
                crowdfund=crowdfund,
                amount=amount,
                name=name,
                show=False
            )
            crowdfund.payment_received += Decimal(amount)
            crowdfund.save()
            messages.success(request, 'You contributed $%.2f. Thanks!' % amount)
            messages.info(request, 'To track this request, click Follow below.')
            log_msg = ('%s has contributed to crowdfund', name)
            logger.info(log_msg)
        except stripe.CardError as exc:
            msg = 'Payment error. Your card has not been charged'
            messages.error(request, msg)
            logger.error('Payment error: %s', exc, exc_info=sys.exc_info())
    return redirect(redirect_url)

def contribute_project(request, idx):
    """Contribute to a crowdfunding project"""
    crowdfund = get_object_or_404(CrowdfundProject, pk=idx)
    redirect_url = reverse(
        'project-detail',
        kwargs={'slug': crowdfund.project.slug, 'idx': crowdfund.project.pk}
    )
    return _contribute(
        request,
        crowdfund,
        CrowdfundProjectPayment,
        redirect_url
    )

def project_detail(request, slug, idx):
    """Project details"""
    project = get_object_or_404(CrowdfundProject, slug=slug, pk=idx)
    return render_to_response(
        'crowdfund/project_detail.html',
        {'project': project},
        context_instance=RequestContext(request)
    )
