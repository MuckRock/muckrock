"""
Views for the crowdfund application
"""

from django.core.urlresolvers import reverse, NoReverseMatch
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, CreateView

from datetime import date, timedelta
from decimal import Decimal
import logging
import stripe

from muckrock.crowdfund.forms import CrowdfundProjectForm, \
                                     CrowdfundRequestPaymentForm, \
                                     CrowdfundProjectPaymentForm
from muckrock.crowdfund.models import CrowdfundRequest, CrowdfundProject
from muckrock.project.models import Project
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


class CrowdfundDetailView(DetailView):
    """
    Presents details about a crowdfunding campaign,
    as well as providing a private endpoint for contributions.
    """
    form = None

    def get_form(self):
        """Returns a form or None"""
        return self.form

    def get_context_data(self, **kwargs):
        """Adds Stripe public key to context"""
        context = super(CrowdfundDetailView, self).get_context_data(**kwargs)
        context['stripe_pk'] = STRIPE_PUB_KEY
        return context

    def get_redirect_url(self):
        """Returns a url to redirect to"""
        try:
            crowdfund_object = self.get_object().get_crowdfund_object()
            redirect_url = crowdfund_object.get_absolute_url()
        except (AttributeError, NoReverseMatch) as exception:
            logging.error(exception)
            redirect_url = reverse('index')
        return redirect_url

    def return_error(self, request):
        """If AJAX, return HTTP 400 ERROR. Else, add a message to the session."""
        if request.is_ajax():
            return HttpResponse(400)
        else:
            messages.error(
                request,
                ('There was an error making your contribution. '
                'Your card has not been charged.')
            )
            return redirect(self.get_redirect_url())

    def post(self, request, **kwargs):
        """
        First we validate the payment form, so we don't charge someone's card by accident.
        Next, we charge their card. Finally, use the validated payment form to create and
        return a CrowdfundRequestPayment object.
        """
        crowdfund = request.POST.get('crowdfund')
        if crowdfund != kwargs['pk']:
            error_msg = ('The crowdfund associated with the payment and the crowdfund '
                         'associated with this page do not match.')
            logging.error(error_msg)
            self.return_error(request)
        amount = request.POST.get('amount')
        show = request.POST.get('show')
        email = request.POST.get('email')
        token = request.POST.get('token')
        user = request.user if request.user.is_authenticated() else None
        crowdfund_object = get_object_or_404(self.model, pk=crowdfund)
        amount = Decimal(float(amount)/100)
        # check if the amount is greater than the amount required
        # if it is, only charge the amount required
        if amount > crowdfund_object.amount_remaining():
            amount = crowdfund_object.amount_remaining()
        payment_data = {'amount': amount, 'show': show, 'crowdfund': crowdfund}
        payment_form = self.get_form()
        try:
            payment_form = payment_form(payment_data)
        except TypeError:
            logging.error(('The subclassed object does not have a form attribute '
                           'so no payments can be made.'))
            raise ValueError('%s does not have its form attribute set.' % self.__class__)
        payment_object = None
        if payment_form.is_valid() and email and token:
            if process_payment(request, amount, token, crowdfund_object):
                payment_object = payment_form.save(commit=False)
                payment_object.user = user
                payment_object.save()
                logging.info(payment_object)
                crowdfund_object.update_payment_received()
                # log the payment
                log_msg = """
                    -:- Crowdfund Payment -:-
                    Amount:      %s
                    Email:       %s
                    Token:       %s
                    Show:        %s
                    Crowdfund:   %s
                    User:        %s
                """
                logging.info(log_msg, amount, email, token, show, crowdfund, user)
                # if AJAX, return HTTP 200 OK
                # else, add a message to the session
                if request.is_ajax():
                    return HttpResponse(200)
                else:
                    messages.success(request, 'Thank you for your contribution!')
                    return redirect(self.get_redirect_url())
        self.return_error(request)

class CrowdfundRequestDetail(CrowdfundDetailView):
    """Specificies a detail view for crowdfunding requests."""
    model = CrowdfundRequest
    form = CrowdfundRequestPaymentForm
    template_name = 'crowdfund/request_detail.html'

class CrowdfundProjectDetail(CrowdfundDetailView):
    """Specifies a detail view for crowdfunding projects."""
    model = CrowdfundProject
    form = CrowdfundProjectPaymentForm
    template_name = 'crowdfund/project_detail.html'

class CrowdfundProjectCreateView(CreateView):
    """A creation view for project crowdfunding"""
    model = CrowdfundProject
    form_class = CrowdfundProjectForm
    template_name = 'project/crowdfund.html'

    def get_project(self):
        """Returns the project based on the URL keyword arguments"""
        return self.get_object(queryset=Project.objects.all())

    def get_initial(self):
        """Sets defaults in crowdfund project form"""
        project = self.get_project()
        initial_name = 'Crowdfund the ' + project.title
        initial_date = date.today() + timedelta(30)
        return {
            'name': initial_name,
            'date_due': initial_date,
            'project': project.id
        }

    def get_success_url(self):
        project = self.get_project()
        return project.get_absolute_url()
