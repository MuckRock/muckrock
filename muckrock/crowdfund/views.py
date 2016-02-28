"""
Views for the crowdfund application
"""

from django.conf import settings
from django.core.urlresolvers import reverse, NoReverseMatch
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView

import actstream
from datetime import date, timedelta
import logging
import stripe

from muckrock.crowdfund.forms import CrowdfundForm, CrowdfundPaymentForm
from muckrock.crowdfund.models import Crowdfund
from muckrock.project.models import Project

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY


class CrowdfundListView(ListView):
    """Lists active crowdfunds"""
    model = Crowdfund
    template_name = 'crowdfund/list.html'

    def get_context_data(self, **kwargs):
        """Add title and other data to context"""
        context = super(CrowdfundListView, self).get_context_data(**kwargs)
        context['title'] = 'Crowdfund campaigns needing funding'
        return context

    def get_queryset(self):
        """Only list open crowdfunds on unembargoed requests"""
        queryset = super(CrowdfundListView, self).get_queryset()
        queryset = queryset.exclude(closed=True).exclude(date_due__lt=date.today())
        user = self.request.user
        if not user.is_staff and user.is_authenticated():
            queryset = (queryset
                .filter(Q(foia__embargo=False) | Q(foia__user=user))
                .filter(Q(project__private=False) | Q(project__contributors=user)))
        elif not user.is_staff:
            queryset = queryset.filter(
                    foia__embargo=False, project__private=False)
        return queryset


class CrowdfundDetailView(DetailView):
    """
    Presents details about a crowdfunding campaign,
    as well as providing a private endpoint for contributions.
    """
    model = Crowdfund
    form = CrowdfundPaymentForm
    template_name = 'crowdfund/detail.html'

    def get_form(self):
        """Returns a form or None"""
        return self.form

    def get_context_data(self, **kwargs):
        """Adds Stripe public key to context"""
        context = super(CrowdfundDetailView, self).get_context_data(**kwargs)
        context['stripe_pk'] = settings.STRIPE_PUB_KEY
        return context

    def get_redirect_url(self):
        """Returns a url to redirect to"""
        redirect_url = reverse('index')
        try:
            crowdfund_object = self.get_object().get_crowdfund_object()
            redirect_url = crowdfund_object.get_absolute_url()
        except (AttributeError, NoReverseMatch) as exception:
            logging.error(exception)
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
        token = request.POST.get('token')
        email = request.POST.get('email')
        try:
            payment_form = self.get_form()
            # pylint:disable=not-callable
            payment_form = payment_form(request.POST)
            # pylint:enable=not-callable
        except TypeError:
            logging.error(('The subclassed object does not have a form attribute '
                           'so no payments can be made.'))
            raise ValueError('%s does not have its form attribute set.' % self.__class__)
        if payment_form.is_valid() and token:
            cleaned_data = payment_form.cleaned_data
            crowdfund = cleaned_data['crowdfund']
            amount = cleaned_data['amount']
            show = cleaned_data['show']
            user = request.user if request.user.is_authenticated() else None
            stripe_exceptions = (
                stripe.InvalidRequestError,
                stripe.CardError,
                stripe.APIConnectionError,
                stripe.AuthenticationError
            )
            try:
                crowdfund.make_payment(token, email, amount, show, user)
            except stripe_exceptions as payment_error:
                logging.warn(payment_error)
                self.return_error(request)
            # if AJAX, return HTTP 200 OK
            # else, add a message to the session
            if request.is_ajax():
                return HttpResponse(200)
            else:
                messages.success(request, 'Thank you for your contribution!')
                return redirect(self.get_redirect_url())
        return self.return_error(request)


class CrowdfundProjectCreateView(CreateView):
    """A creation view for project crowdfunding"""
    model = Crowdfund
    form_class = CrowdfundForm
    template_name = 'project/crowdfund.html'

    @method_decorator(login_required)
    @method_decorator(user_passes_test(lambda u: u.is_staff))
    def dispatch(self, *args, **kwargs):
        """At the moment, only staff are allowed to create a project crowdfund."""
        return super(CrowdfundProjectCreateView, self).dispatch(*args, **kwargs)

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
        """Generates actions before returning URL"""
        crowdfund = self.get_object()
        project = self.get_project()
        actstream.action.send(
            self.request.user,
            varb='started',
            action_object=crowdfund,
            target=project
        )
        return project.get_absolute_url()

