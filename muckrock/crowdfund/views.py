"""
Views for the crowdfund application
"""

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.views.generic.detail import DetailView

from decimal import Decimal
import logging
import stripe
import sys

from muckrock.crowdfund.models import \
    CrowdfundRequest, \
    CrowdfundProject, \
    CrowdfundRequestPayment, \
    CrowdfundProjectPayment
from muckrock.settings import STRIPE_SECRET_KEY

logger = logging.getLogger(__name__)
stripe.api_key = STRIPE_SECRET_KEY

class CrowdfundRequestDetail(DetailView):
    """
    Presents details about a crowdfunding campaign,
    as well as providing a private endpoint for contributions
    """
    model = CrowdfundRequest
    template_name = 'details/crowdfund_request_detail.html'

    """

    def post(self, request):
        if request.is_ajax():
            return HttpResponse(200)
        else:
            return render_to_response(self)


    amount = request.POST.get('amount')
    token = request.POST.get('stripe_token')
    if amount and token:
        form = CrowdfundRequestPaymentForm(request.POST, initial={'crowdfund': crowdfund})
        if form.is_valid():
            payment = form.save(commit=False)
            if request.user.is_authenticated():
                payment.user = request.user
                payment.name = request.user.get_full_name()
                payment.save()
            try:
                stripe.Charge.create(
    """


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
