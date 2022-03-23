"""
Views for muckrock project
"""
# Django
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.utils import lookup_needs_distinct
from django.contrib.auth.decorators import user_passes_test
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.core.exceptions import ImproperlyConfigured
from django.db.models import F, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.html import escape
from django.views.generic import FormView, ListView, TemplateView, View

# Standard Library
import logging
import operator
import sys
from functools import reduce

# Third Party
import stripe
from dal import autocomplete
from watson import search as watson
from watson.views import SearchMixin

# MuckRock
from muckrock.accounts.models import RecurringDonation
from muckrock.accounts.utils import (
    mailchimp_subscribe,
    mixpanel_event,
    stripe_get_customer,
)
from muckrock.agency.models import Agency
from muckrock.core.forms import NewsletterSignupForm, SearchForm, StripeForm
from muckrock.core.utils import stripe_retry_on_error
from muckrock.foia.models import FOIAFile, FOIARequest
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.news.models import Article
from muckrock.project.models import Project

logger = logging.getLogger(__name__)


class OrderedSortMixin:
    """Sorts and orders a queryset given some inputs."""

    default_sort = "id"
    default_order = "asc"
    sort_map = {}

    def sort_queryset(self, queryset):
        """
        Sorts a queryset of objects.

        We need to make sure the field to sort by is allowed.
        If the field isn't allowed, return the default order queryset.
        """
        # pylint:disable=protected-access
        sort = self.request.GET.get("sort", self.default_sort)
        order = self.request.GET.get("order", self.default_order)
        sort = self.sort_map.get(sort, self.default_sort)
        if order == "desc":
            sort = F(sort).desc()
        else:
            sort = F(sort).asc()
        return queryset.order_by(sort)

    def get_queryset(self):
        """Sorts the queryset before returning it."""
        return self.sort_queryset(super(OrderedSortMixin, self).get_queryset())

    def get_context_data(self, **kwargs):
        """Adds sort and order data to the context."""
        context = super(OrderedSortMixin, self).get_context_data(**kwargs)
        context["sort"] = self.request.GET.get("sort", self.default_sort)
        context["order"] = self.request.GET.get("order", self.default_order)
        return context


class ModelFilterMixin:
    """
    The ModelFilterMixin gives the ability to filter a list
    of objects with the help of the django_filters library.

    It requires a filter_class be defined.
    """

    filter_class = None

    def get_filter(self):
        """Initializes and returns the filter, if a filter_class is defined."""
        # pylint:disable=not-callable
        if self.filter_class is None:
            raise AttributeError("Missing a filter class.")
        return self.filter_class(
            self.request.GET, queryset=self.get_queryset(), request=self.request
        )

    def get_context_data(self, **kwargs):
        """
        Adds the filter to the context and overrides the
        object_list value with the filter's queryset.
        We also apply pagination to the filter queryset.
        """
        filter_ = self.get_filter()
        queryset = filter_.qs
        print("filter", filter_.data)
        if any(filter_.data.values()):
            print("distinct on!")
            queryset = queryset.distinct()

        context = super(ModelFilterMixin, self).get_context_data(
            object_list=queryset, **kwargs
        )
        context["filter"] = filter_

        return context


class PaginationMixin:
    """
    The PaginationMixin provides pagination support on a generic ListView,
    but also allows the per_page value to be adjusted with URL arguments.
    """

    paginate_by = 25
    min_per_page = 5
    max_per_page = 100

    def get_paginate_by(self, queryset):
        """Allows paginate_by to be set by a query argument."""
        # pylint:disable=unused-argument
        try:
            per_page = int(self.request.GET.get("per_page"))
            return max(min(per_page, self.max_per_page), self.min_per_page)
        except (ValueError, TypeError):
            return self.paginate_by

    def get_context_data(self, **kwargs):
        """Adds per_page to the context"""
        context = super(PaginationMixin, self).get_context_data(**kwargs)
        context["per_page"] = self.get_paginate_by(self.get_queryset())
        return context


class ModelSearchMixin:
    """
    The ModelSearchMixin allows a queryset provided by a list view to be
    searched, using the watson library.
    """

    search_form = SearchForm

    def get_query(self):
        """Gets the query from the request, if it exists."""
        return self.request.GET.get("q")

    def get_queryset(self):
        """
        If there is a search query provided in the request,
        then filter the queryset with a search.
        """
        queryset = super(ModelSearchMixin, self).get_queryset()
        query = self.get_query()
        if query:
            queryset = watson.filter(queryset.model, query)
        return queryset

    def get_context_data(self, **kwargs):
        """Adds the query to the context."""
        context = super(ModelSearchMixin, self).get_context_data(**kwargs)
        query = self.get_query()
        context["query"] = query
        context["search_form"] = self.search_form(initial={"q": query})
        return context


class MRListView(PaginationMixin, ListView):
    """Defines a title and base template for our list views."""

    title = ""
    template_name = "base_list.html"

    def get_context_data(self, **kwargs):
        """Adds title to the context data."""
        context = super(MRListView, self).get_context_data(**kwargs)
        context["title"] = self.title
        return context


class MROrderedListView(OrderedSortMixin, MRListView):
    """Adds ordering to a list view."""


class MRFilterListView(OrderedSortMixin, ModelFilterMixin, MRListView):
    """Adds ordered sorting and filtering to a MRListView."""


class MRSearchFilterListView(
    OrderedSortMixin, ModelSearchMixin, ModelFilterMixin, MRListView
):
    """Adds ordered sorting, searching, and filtering to a MRListView."""


class SearchView(SearchMixin, MRListView):
    """Always lower case queries for case insensitive searches"""

    title = "Search"
    template_name = "search.html"
    context_object_name = "object_list"

    def get_queryset(self):
        """Select related content types"""
        return (
            super(SearchView, self)
            .get_queryset()
            .order_by("id")
            .select_related("content_type")
        )


class NewsletterSignupView(View):
    """Allows users to signup for our MailChimp newsletter."""

    def redirect_url(self, request):
        """If a next url is provided, redirect there. Otherwise, redirect to the index."""
        next_ = request.GET.get("next", "index")
        return redirect(next_)

    def post(self, request, *_args, **_kwargs):
        """Check if the form is valid and then pass it on to our form handling
        functions."""
        form = NewsletterSignupForm(request.POST)
        if not form.is_valid():
            return self.form_invalid(request, form)
        else:
            return self.form_valid(request, form)

    def form_invalid(self, request, form):
        """If the form is invalid, then either a bad or no email was provided."""
        email = form.data.get("email")
        # if they provided an email, then it is invalid
        # if they didn't, then they're just being dumb!
        if email:
            # email needs to be escaped as messages are marked as safe
            # and email is user supplied - failure to do so is a
            # XSS vulnerability
            msg = "%s is not a valid email address." % escape(email)
        else:
            msg = "You forgot to enter an email!"
        messages.error(request, msg)
        return self.redirect_url(request)

    def form_valid(self, request, form):
        """If the form is valid, try subscribing the email to our MailChimp newsletters."""
        email = form.cleaned_data["email"]
        list_ = form.cleaned_data["list"]
        default = form.cleaned_data["default"]
        default_list = settings.MAILCHIMP_LIST_DEFAULT if default else None
        # First try subscribing the user to the list they are signing up for.
        path = request.GET.get("next", request.path)
        url = "{}{}".format(settings.MUCKROCK_URL, path)
        primary_error = mailchimp_subscribe(
            request, email, list_, source="Newsletter Sign Up Form", url=url
        )
        # Add the user to the default list if they want to be added.
        # If an error occurred with the first subscription,
        # don't try signing up for the default list.
        # If an error occurs with this subscription, don't worry about it.
        if default_list is not None and default_list != list_ and not primary_error:
            mailchimp_subscribe(
                request,
                email,
                default_list,
                suppress_msg=True,
                source="Newsletter Sign Up Form",
                url=url,
            )
        return self.redirect_url(request)


class LandingView(TemplateView):
    """Renders the landing page template."""

    template_name = "flatpages/landing.html"


class Homepage:
    """Control caching for the homepage"""

    def get_cached_values(self):
        """Return all the methods used to generate the cached values"""
        return [
            ("articles", self.articles),
            ("featured_projects", self.featured_projects),
            ("completed_requests", self.completed_requests),
            ("stats", self.stats),
        ]

    def articles(self):
        """Get the articles for the front page"""
        return Article.objects.get_published().prefetch_authors()[:5]

    def featured_projects(self):
        """Get the featured projects for the front page"""
        return Project.objects.get_public().optimize().filter(featured=True)[:4]

    def completed_requests(self):
        """Get recently completed requests"""
        return lambda: (
            FOIARequest.objects.get_public()
            .get_done()
            .order_by("-datetime_done", "pk")
            .select_related(
                "agency__jurisdiction__parent__parent", "composer__user__profile"
            )
            .only(
                "status",
                "slug",
                "title",
                "agency__name",
                "agency__slug",
                "agency__jurisdiction__slug",
                "agency__jurisdiction__level",
                "agency__jurisdiction__name",
                "agency__jurisdiction__parent__abbrev",
                "agency__jurisdiction__parent__name",
                "agency__jurisdiction__parent__slug",
                "agency__jurisdiction__parent__parent__slug",
                "composer__user__username",
                "composer__user__profile__full_name",
            )
            .get_public_file_count(limit=6)
        )

    def stats(self):
        """Get some stats to show on the front page"""
        # pylint: disable=unnecessary-lambda
        return {
            "request_count": lambda: FOIARequest.objects.count(),
            "completed_count": lambda: FOIARequest.objects.get_done().count(),
            "page_count": lambda: FOIAFile.objects.aggregate(pages=Sum("pages"))[
                "pages"
            ],
            "agency_count": lambda: Agency.objects.get_approved().count(),
        }


def homepage(request):
    """Get all the details needed for the homepage"""
    context = {}
    for name, value in Homepage().get_cached_values():
        context[name] = value()
    return render(request, "homepage.html", context)


@user_passes_test(lambda u: u.is_staff)
def reset_homepage_cache(request):
    """Reset the homepage cache"""
    # pylint: disable=unused-argument

    template_keys = ("homepage_top", "homepage_bottom", "dropdown_recent_articles")
    for key in template_keys:
        cache.delete(make_template_fragment_key(key))

    return redirect("index")


class StripeFormMixin:
    """Prefills the StripeForm values."""

    def get_initial(self):
        """Add initial data to the form."""
        initial = super(StripeFormMixin, self).get_initial()
        initial["stripe_pk"] = settings.STRIPE_PUB_KEY
        initial["stripe_label"] = "Buy"
        initial["stripe_description"] = ""
        initial["stripe_fee"] = 0
        initial["stripe_bitcoin"] = True
        return initial


class DonationFormView(StripeFormMixin, FormView):
    """Accepts donations from all users."""

    form_class = StripeForm
    template_name = "forms/donate.html"

    def get_initial(self):
        """Adds the user's email to the form if they're logged in."""
        user = self.request.user
        email = ""
        if user.is_authenticated:
            email = user.email
        return {
            "stripe_email": email,
            "stripe_label": "Donate",
            "stripe_description": "Tax Deductible Donation",
        }

    def form_valid(self, form):
        """If the form is valid, charge the token provided by the form, then
        send a receipt."""
        token = form.cleaned_data["stripe_token"]
        email = form.cleaned_data["stripe_email"]
        amount = form.cleaned_data["stripe_amount"]
        type_ = form.cleaned_data["type"]
        if type_ == "one-time":
            charge = self.make_charge(token, amount, email)
            if charge is None:
                return self.form_invalid(form)
        elif type_ == "monthly":
            subscription = self.make_subscription(token, amount, email)
            if subscription is None:
                return self.form_invalid(form)
        return super(DonationFormView, self).form_valid(form)

    def get_success_url(self):
        """Return a redirection the donation page, always."""
        return reverse("donate-thanks")

    def make_charge(self, token, amount, email):
        """Make a Stripe charge and catch any errors."""
        charge = None
        error_msg = None
        try:
            charge = stripe_retry_on_error(
                stripe.Charge.create,
                amount=amount,
                currency="usd",
                source=token,
                description="Donation from %s" % email,
                metadata={"email": email, "action": "donation"},
                idempotency_key=True,
            )
        except stripe.error.CardError:
            # card declined
            logger.warning("Card was declined.")
            error_msg = "Your card was declined"
        except (
            stripe.error.InvalidRequestError,
            # Invalid parameters were supplied to Stripe's API
            stripe.error.AuthenticationError,
            # Authentication with Stripe's API failed
            stripe.error.APIConnectionError,
            # Network communication with Stripe failed
            stripe.error.StripeError,  # Generic error
        ) as exception:
            logger.error(exception, exc_info=sys.exc_info())
            error_msg = "Oops, something went wrong on our end. Sorry about that!"
        finally:
            if error_msg:
                messages.error(self.request, error_msg)
            else:
                self.request.session["donated"] = amount
                self.request.session["ga"] = "donation"
                mixpanel_event(
                    self.request,
                    "Donate",
                    {"Amount": amount / 100},
                    charge=amount / 100,
                )
        return charge

    def make_subscription(self, token, amount, email):
        """Start a subscription for recurring donations"""
        subscription = None
        quantity = amount / 100
        customer = stripe_get_customer(email, "Donation for {}".format(email))
        if self.request.user.is_authenticated:
            user = self.request.user
        else:
            user = None
        try:
            subscription = stripe_retry_on_error(
                customer.subscriptions.create,
                plan="donate",
                source=token,
                quantity=quantity,
                idempotency_key=True,
            )
        except stripe.error.CardError:
            logger.warning("Card was declined.")
            messages.error(self.request, "Your card was declined")
        except stripe.error.StripeError as exception:
            logger.error(exception, exc_info=sys.exc_info())
            messages.error(
                self.request, "Oops, something went wrong on our end. Sorry about that!"
            )
        else:
            RecurringDonation.objects.create(
                user=user,
                email=email,
                amount=quantity,
                customer_id=customer.id,
                subscription_id=subscription.id,
            )
            mixpanel_event(self.request, "Recurring Donation", {"Amount": quantity})
        return subscription


class DonationThanksView(TemplateView):
    """Returns a thank you message to the user."""

    template_name = "forms/donate_thanks.html"


def jurisdiction(request, jurisdiction=None, slug=None, idx=None, view=None):
    """Redirect to the jurisdiction page"""
    # pylint: disable=redefined-outer-name
    # pylint: disable=unused-argument

    if jurisdiction and idx:
        jmodel = get_object_or_404(Jurisdiction, slug=jurisdiction, pk=idx)
    if idx:
        jmodel = get_object_or_404(Jurisdiction, pk=idx)

    if not view:
        return redirect(jmodel)
    else:
        return redirect(jmodel.get_url(view))


def handler500(request):
    """
    500 error handler which includes request in the context.

    Templates: `500.html`
    Context: None
    """
    return render(request, "500.html", status=500)


# http://stackoverflow.com/a/8429311
def class_view_decorator(function_decorator):
    """Convert a function based decorator into a class based decorator usable
    on class based Views.

    Can't subclass the `view` as it breaks inheritance (super in particular),
    so we monkey-patch instead.
    """

    def simple_decorator(view):
        """Wrap the dispatch method"""
        view.dispatch = method_decorator(function_decorator)(view.dispatch)
        return view

    return simple_decorator


class MRAutocompleteView(autocomplete.Select2QuerySetView):
    """Autocomplete view customized for our use"""

    search_fields = []
    split_words = None
    template = None

    def get_queryset(self):
        """Get the queryset"""
        if self.queryset is not None:
            queryset = self.queryset.all()
        elif self.model is not None:
            # pylint: disable=protected-access
            queryset = self.model._default_manager.all()
        else:
            raise ImproperlyConfigured

        queryset = self.get_search_results(queryset, self.q)

        return queryset

    def get_search_fields(self):
        """The fields to search over"""
        return self.search_fields

    def get_search_results(self, queryset, search_term):
        """
        Return a tuple containing a queryset to implement the search
        and a boolean indicating if the results may contain duplicates.
        """

        def construct_search(field_name):
            """Apply keyword searches"""
            if field_name.startswith("^"):
                return "{}__istartswith".format(field_name[1:])
            elif field_name.startswith("="):
                return "{}__iexact".format(field_name[1:])
            elif field_name.startswith("@"):
                return "{}__search".format(field_name[1:])
            else:
                return "{}__icontains".format(field_name)

        search_fields = self.get_search_fields()
        if search_fields and search_term:
            orm_lookups = [
                construct_search(str(search_field)) for search_field in search_fields
            ]
            if self.split_words is not None:
                word_conditions = []
                for word in search_term.split():
                    or_queries = [Q(**{orm_lookup: word}) for orm_lookup in orm_lookups]
                    word_conditions.append(reduce(operator.or_, or_queries))
                op_ = operator.or_ if self.split_words == "or" else operator.and_
                if word_conditions:
                    queryset = queryset.filter(reduce(op_, word_conditions))
            else:
                or_queries = [
                    Q(**{orm_lookup: search_term}) for orm_lookup in orm_lookups
                ]
                queryset = queryset.filter(reduce(operator.or_, or_queries))

            for search_spec in orm_lookups:
                if lookup_needs_distinct(queryset.model._meta, search_spec):
                    queryset = queryset.distinct()
                    break

        return queryset

    def get_result_label(self, result):
        """Render the choice from an optional HTML template"""
        if self.template:
            return render_to_string(self.template, {"choice": result})
        else:
            return str(result)

    def get_selected_result_label(self, result):
        """Do not use HTML template for selected label"""
        return str(result)
