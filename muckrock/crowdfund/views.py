"""
Views for the crowdfund application
"""

# Django
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import NoReverseMatch, reverse
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic import DetailView, ListView

# Standard Library
import logging
from datetime import date

# Third Party
import requests
import stripe

# MuckRock
from muckrock.accounts.mixins import MiniregMixin
from muckrock.accounts.utils import mixpanel_event, validate_stripe_email
from muckrock.crowdfund.forms import CrowdfundPaymentForm
from muckrock.crowdfund.models import Crowdfund

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY


class CrowdfundListView(ListView):
    """Lists active crowdfunds"""

    model = Crowdfund
    template_name = "crowdfund/list.html"

    def get_context_data(self, **kwargs):
        """Add title and other data to context"""
        context = super(CrowdfundListView, self).get_context_data(**kwargs)
        context["title"] = "Crowdfund campaigns needing funding"
        return context

    def get_queryset(self):
        """Only list open crowdfunds on unembargoed requests"""
        queryset = super(CrowdfundListView, self).get_queryset()
        queryset = queryset.exclude(closed=True).exclude(date_due__lt=date.today())
        user = self.request.user
        if not user.is_staff and user.is_authenticated:
            queryset = queryset.filter(
                Q(foia__embargo=False)
                | Q(foia__composer__user=user)
                | Q(projectcrowdfunds__project__private=False)
                | Q(projectcrowdfunds__project__contributors=user)
            ).distinct()
        elif not user.is_staff:
            queryset = queryset.filter(
                foia__embargo=False, projectcrowdfunds__project__private=False
            )
        return queryset


class CrowdfundDetailView(MiniregMixin, DetailView):
    """
    Presents details about a crowdfunding campaign,
    as well as providing a private endpoint for contributions.
    """

    model = Crowdfund
    template_name = "crowdfund/detail.html"
    minireg_source = "Crowdfund"
    field_map = {"full_name": "name"}

    def get_context_data(self, **kwargs):
        """Adds Stripe public key to context"""
        context = super(CrowdfundDetailView, self).get_context_data(**kwargs)
        context["stripe_pk"] = settings.STRIPE_PUB_KEY
        return context

    def get_redirect_url(self):
        """Returns a url to redirect to"""
        redirect_url = reverse("index")
        try:
            crowdfund_object = self.get_object().get_crowdfund_object()
            redirect_url = crowdfund_object.get_absolute_url()
        except (AttributeError, NoReverseMatch) as exception:
            logger.error(exception)
        return redirect_url

    def return_error(self, request, error=None):
        """If AJAX, return HTTP 400 ERROR. Else, add a message to the session."""
        error_msg = (
            "There was an error making your contribution. "
            "Your card has not been charged."
        )
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"message": error_msg, "error": str(error)}, status=400)
        else:
            messages.error(request, error_msg)
            return redirect(self.get_redirect_url())

    def post(self, request, **kwargs):
        """
        First we validate the payment form, so we don't charge someone's card by
        accident.
        Next, we charge their card. Finally, use the validated payment form to create
        and return a CrowdfundRequestPayment object.
        """
        # pylint: disable=too-many-locals
        token = request.POST.get("stripe_token")
        email = request.POST.get("stripe_email")
        email = validate_stripe_email(email)

        payment_form = CrowdfundPaymentForm(request.POST)
        if payment_form.is_valid() and token and email:
            amount = payment_form.cleaned_data["stripe_amount"]
            # If there is no user but the show and full_name fields are filled in,
            # and a user with that email does not already exists, create the
            # user with our "miniregistration" functionality and then log them in
            user = request.user if request.user.is_authenticated else None
            registered = False
            show = payment_form.cleaned_data["show"]
            full_name = payment_form.cleaned_data["full_name"]
            email_exists = User.objects.filter(email__iexact=email).exists()
            if user is None and show and full_name and not email_exists:
                try:
                    user = self.miniregister(payment_form, full_name, email)
                except requests.exceptions.RequestException:
                    return self.return_error(request)
                registered = True
            crowdfund = payment_form.cleaned_data["crowdfund"]
            if crowdfund.expired():
                return self.return_error(request)
            try:
                if crowdfund.can_recur() and payment_form.cleaned_data["recurring"]:
                    crowdfund.make_recurring_payment(token, email, amount, show, user)
                    event = "Recurring Crowdfund Payment"
                    kwargs = {}
                else:
                    crowdfund.make_payment(token, email, amount, show, user)
                    event = "Crowdfund Payment"
                    kwargs = {"charge": float(amount)}
            except stripe.StripeError as payment_error:
                logger.warning(payment_error)
                return self.return_error(request, payment_error)
            else:
                mixpanel_event(
                    request,
                    event,
                    {
                        "Amount": float(amount),
                        "Crowdfund": crowdfund.name,
                        "Crowdfund ID": crowdfund.pk,
                        "Show": show,
                    },
                    **kwargs
                )
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                data = {
                    "authenticated": user.is_authenticated if user else False,
                    "registered": registered,
                }
                return JsonResponse(data, status=200)
            else:
                messages.success(request, "Thank you for your contribution!")
                return redirect(self.get_redirect_url())
        return self.return_error(request)


@method_decorator(xframe_options_exempt, name="dispatch")
class CrowdfundEmbedView(DetailView):
    """Presents an embeddable view for a single file."""

    model = Crowdfund
    template_name = "crowdfund/embed.html"
