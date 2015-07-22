"""
Views for the crowdfund application
"""

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic.detail import DetailView

from decimal import Decimal
import logging
import stripe

from muckrock.crowdfund.forms import CrowdfundRequestPaymentForm
from muckrock.crowdfund.models import CrowdfundRequest
from muckrock.settings import STRIPE_SECRET_KEY, STRIPE_PUB_KEY

logger = logging.getLogger(__name__)
stripe.api_key = STRIPE_SECRET_KEY

def process_payment(request, amount, token, crowdfund):
    """Helper function to create a Stripe charge and handle errors"""
    # double -> int conversion
    # http://stackoverflow.com/a/13528445/4256689
    amount = int(amount) * 100
    logging.debug(amount)
    try:
        stripe.Charge.create(
            amount=amount,
            source=token,
            currency='usd',
            description='Contribute to Crowdfunding: %s %s' %
                (crowdfund, crowdfund.pk),
        )
        return True
    except (
        stripe.InvalidRequestError,
        stripe.CardError,
        stripe.APIConnectionError,
        stripe.AuthenticationError
    ) as exception:
        logging.error('Processing a Stripe charge: %s', exception)
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
        # pylint: disable=no-self-use
        # pylint: disable=unused-variable
        context = super(CrowdfundRequestDetail, self).get_context_data(**kwargs)
        context['stripe_pk'] = STRIPE_PUB_KEY
        return context

    def post(self, request, **kwargs):
        """
        First we validate the payment form, so we don't charge someone's card by accident.
        Next, we charge their card. Finally, use the validated payment form to create and
        return a CrowdfundRequestPayment object.
        """
        # pylint: disable=unused-argument
        # pylint: disable=no-self-use
        amount = request.POST.get('amount')
        show = request.POST.get('show')
        crowdfund = request.POST.get('crowdfund')
        email = request.POST.get('email')
        token = request.POST.get('token')
        user = None
        if request.user.is_authenticated():
            user = request.user
        logging.debug(user)
        crowdfund_object = get_object_or_404(CrowdfundRequest, pk=crowdfund)

        log_msg = '\n\
                   --- Crowdfunding Payment ---\n\
                   Amount:      %s\n\
                   Email:       %s\n\
                   Token:       %s\n\
                   Show:        %s\n\
                   Crowdfund:   %s\n\
                   User:        %s\n\
                   \n'

        logging.info(log_msg, amount, email, token, show, crowdfund, user)

        amount = Decimal(float(amount)/100)
        # check if the amount is greater than the amount required
        # if it is, only charge the amount required
        if amount > crowdfund_object.amount_remaining():
            amount = crowdfund_object.amount_remaining()

        payment_data = {'amount': amount, 'show': show, 'crowdfund': crowdfund}
        payment_form = CrowdfundRequestPaymentForm(payment_data)
        payment_object = None
        if payment_form.is_valid() and email and token:
            if process_payment(request, amount, token, crowdfund_object):
                payment_object = payment_form.save(commit=False)
                payment_object.user = user
                payment_object.save()
                logging.info(payment_object)
                crowdfund_object.update_payment_received()
                # if AJAX, return HTTP 200 OK
                # else, add a message to the session
                if request.is_ajax():
                    return HttpResponse(200)
                else:
                    messages.success(request, 'Thank you for your contribution!')
                    return redirect(crowdfund_object.foia)
        # if AJAX, return HTTP 400 ERROR
        # else, add a message to the session
        if request.is_ajax():
            return HttpResponse(400)
        else:
            messages.error(
                request,
                ('There was an error making your contribution. '
                'Your card has not been charged.')
            )
            return redirect(crowdfund_object.foia)
