"""
Views for muckrock project
"""
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.core.urlresolvers import reverse
from django.db.models import Sum
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.utils.html import escape
from django.views.generic import View, ListView, FormView, TemplateView

from muckrock.accounts.models import RecurringDonation
from muckrock.agency.models import Agency
from muckrock.foia.models import FOIARequest, FOIAFile
from muckrock.forms import NewsletterSignupForm, SearchForm, StripeForm
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.message.tasks import send_charge_receipt
from muckrock.news.models import Article
from muckrock.project.models import Project
from muckrock.utils import stripe_retry_on_error, retry_on_error

import logging
import requests
import stripe
import sys
from watson import search as watson
from watson.views import SearchMixin

logger = logging.getLogger(__name__)


class OrderedSortMixin(object):
    """Sorts and orders a queryset given some inputs."""
    default_sort = 'id'
    default_order = 'asc'
    sort_map = {}

    def sort_queryset(self, queryset):
        """
        Sorts a queryset of objects.

        We need to make sure the field to sort by is allowed.
        If the field isn't allowed, return the default order queryset.
        """
        # pylint:disable=protected-access
        sort = self.request.GET.get('sort', self.default_sort)
        order = self.request.GET.get('order', self.default_order)
        sort = self.sort_map.get(sort, self.default_sort)
        if order != 'asc':
            sort = '-' + sort
        return queryset.order_by(sort)

    def get_queryset(self):
        """Sorts the queryset before returning it."""
        return self.sort_queryset(super(OrderedSortMixin, self).get_queryset())

    def get_context_data(self, **kwargs):
        """Adds sort and order data to the context."""
        context = super(OrderedSortMixin, self).get_context_data(**kwargs)
        context['sort'] = self.request.GET.get('sort', self.default_sort)
        context['order'] = self.request.GET.get('order', self.default_order)
        return context


class ModelFilterMixin(object):
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
            raise AttributeError('Missing a filter class.')
        return self.filter_class(
                self.request.GET,
                queryset=self.get_queryset(),
                request=self.request,
                )

    def get_context_data(self, **kwargs):
        """
        Adds the filter to the context and overrides the
        object_list value with the filter's queryset.
        We also apply pagination to the filter queryset.
        """
        context = super(ModelFilterMixin, self).get_context_data(**kwargs)
        _filter = self.get_filter()
        queryset = _filter.qs
        if any(_filter.data.values()):
            queryset = queryset.distinct()
        try:
            page_size = self.get_paginate_by(queryset)
        except AttributeError:
            page_size = 0
        if page_size:
            paginator, page, queryset, is_paginated = self.paginate_queryset(queryset, page_size)
            context.update({
                'filter': _filter,
                'paginator': paginator,
                'page_obj': page,
                'is_paginated': is_paginated,
                'object_list': queryset
            })
        else:
            context.update({
                'filter': _filter,
                'paginator': None,
                'page_obj': None,
                'is_paginated': False,
                'object_list': queryset
            })
        return context


class PaginationMixin(object):
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
            per_page = int(self.request.GET.get('per_page'))
            return max(min(per_page, self.max_per_page), self.min_per_page)
        except (ValueError, TypeError):
            return self.paginate_by

    def get_context_data(self, **kwargs):
        """Adds per_page to the context"""
        context = super(PaginationMixin, self).get_context_data(**kwargs)
        context['per_page'] = self.get_paginate_by(self.get_queryset())
        return context


class ModelSearchMixin(object):
    """
    The ModelSearchMixin allows a queryset provided by a list view to be
    searched, using the watson library.
    """
    search_form = SearchForm

    def get_query(self):
        """Gets the query from the request, if it exists."""
        return self.request.GET.get('q')

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
        context['query'] = query
        context['search_form'] = self.search_form(initial={'q': query})
        return context


class MRListView(PaginationMixin, ListView):
    """Defines a title and base template for our list views."""
    title = ''
    template_name = 'base_list.html'

    def get_context_data(self, **kwargs):
        """Adds title to the context data."""
        context = super(MRListView, self).get_context_data(**kwargs)
        context['title'] = self.title
        return context


class MROrderedListView(OrderedSortMixin, MRListView):
    """Adds ordering to a list view."""
    pass


class MRFilterListView(OrderedSortMixin, ModelFilterMixin, MRListView):
    """Adds ordered sorting and filtering to a MRListView."""
    pass


class MRSearchFilterListView(OrderedSortMixin, ModelSearchMixin, ModelFilterMixin, MRListView):
    """Adds ordered sorting, searching, and filtering to a MRListView."""
    pass


class SearchView(SearchMixin, MRListView):
    """Always lower case queries for case insensitive searches"""
    title = 'Search'
    template_name = 'search.html'
    context_object_name = 'object_list'

    def get_queryset(self):
        """Select related content types"""
        return (super(SearchView, self)
                .get_queryset()
                .order_by('id')
                .select_related('content_type')
                )


class NewsletterSignupView(View):
    """Allows users to signup for our MailChimp newsletter."""
    def get(self, request, *args, **kwargs):
        """Returns a signup form"""
        template = 'forms/newsletter.html'
        context = {'form': NewsletterSignupForm(initial={'list': settings.MAILCHIMP_LIST_DEFAULT})}
        return render(request, template, context)

    def redirect_url(self, request):
        """If a next url is provided, redirect there. Otherwise, redirect to the index."""
        # pylint: disable=no-self-use
        next_ = request.GET.get('next', 'index')
        return redirect(next_)

    def post(self, request, *args, **kwargs):
        """Check if the form is valid and then pass it on to our form handling functions."""
        form = NewsletterSignupForm(request.POST)
        if not form.is_valid():
            return self.form_invalid(request, form)
        else:
            return self.form_valid(request, form)

    def form_invalid(self, request, form):
        """If the form is invalid, then either a bad or no email was provided."""
        _email = form.data['email']
        # if they provided an email, then it is invalid
        # if they didn't, then they're just being dumb!
        if _email:
            # _email needs to be escaped as messages are marked as safe
            # and _email is user supplied - failure to do so is a
            # XSS vulnerability
            msg = '%s is not a valid email address.' % escape(_email)
        else:
            msg = 'You forgot to enter an email!'
        messages.error(request, msg)
        return self.redirect_url(request)

    def form_valid(self, request, form):
        """If the form is valid, try subscribing the email to our MailChimp newsletters."""
        _email = form.cleaned_data['email']
        _list = form.cleaned_data['list']
        _default = form.cleaned_data['default']
        default_list = settings.MAILCHIMP_LIST_DEFAULT if _default else None
        # First try subscribing the user to the list they are signing up for.
        primary_error = False
        try:
            self.subscribe(_email, _list)
            messages.success(request, ('Thank you for subscribing to our newsletter. '
                                       'We sent a confirmation email to your inbox.'))
        except ValueError as exception:
            messages.error(request, exception)
            primary_error = True
        except requests.exceptions.HTTPError as exception:
            messages.error(request, 'Sorry, an error occurred while trying to subscribe you.')
            logging.warning(exception)
            primary_error = True
        # Add the user to the default list if they want to be added.
        # If an error occurred with the first subscription,
        # don't try signing up for the default list.
        # If an error occurs with this subscription, don't worry about it.
        if default_list is not None and default_list != _list and not primary_error:
            try:
                self.subscribe(_email, default_list)
            except (ValueError, requests.exceptions.HTTPError) as exception:
                # suppress the error shown to the user, but still log it
                logging.warning('Secondary signup: %s', exception)
        return self.redirect_url(request)

    def subscribe(self, _email, _list):
        """Adds the email to the mailing list throught the MailChimp API.
        http://developer.mailchimp.com/documentation/mailchimp/reference/lists/members/"""
        # pylint: disable=no-self-use
        api_url = settings.MAILCHIMP_API_ROOT + '/lists/' + _list + '/members/'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'apikey %s' % settings.MAILCHIMP_API_KEY
        }
        data = {
            'email_address': _email,
            'status': 'pending',
        }
        response = retry_on_error(
                requests.ConnectionError,
                requests.post,
                api_url,
                json=data,
                headers=headers,
                )
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as exception:
            # in the case of an error, the status will either be 4XX or 5XX
            # if 4XX, the user did something wrong and should be notified
            # if 5XX, MailChimp did something wrong and it's not our fault
            status = response.status_code/100
            if status == 4:
                # MailChimp should have returned some data to us describing the error
                error_data = response.json()
                error_title = error_data['title']
                if error_title == 'Member Exists':
                    # the member already exists, so we should tell
                    # the user they cannot use this email address
                    raise ValueError('Email is already a member of the list.')
                else:
                    # we don't know how to specifically address this error
                    # so we should just propagate the HTTPError
                    raise exception
            else:
                # We did nothing wrong. Let's just allow the error to propagate.
                raise exception
        return response


class LandingView(TemplateView):
    """Renders the landing page template."""
    template_name = 'flatpages/landing.html'


class Homepage(object):
    """Control caching for the homepage"""
    # pylint: disable=no-self-use

    def get_cached_values(self):
        """Return all the methods used to generate the cached values"""
        return [
                ('articles', self.articles),
                ('featured_projects', self.featured_projects),
                ('completed_requests', self.completed_requests),
                ('stats', self.stats),
                ]

    def articles(self):
        """Get the articles for the front page"""
        return (Article.objects
                .get_published()
                .prefetch_authors()
                [:5])

    def featured_projects(self):
        """Get the featured projects for the front page"""
        return (Project.objects
                .get_public()
                .optimize()
                .filter(featured=True)
                [:4])

    def completed_requests(self):
        """Get recently completed requests"""
        return lambda: (FOIARequest.objects
                .get_public()
                .get_done()
                .order_by('-date_done', 'pk')
                .select_related_view()
                .get_public_file_count(limit=6))

    def stats(self):
        """Get some stats to show on the front page"""
        return {
                'request_count':
                    lambda: FOIARequest.objects.exclude(status='started').count(),
                'completed_count':
                    lambda: FOIARequest.objects.get_done().count(),
                'page_count':
                    lambda: FOIAFile.objects.aggregate(pages=Sum('pages'))['pages'],
                'agency_count':
                    lambda: Agency.objects.get_approved().count(),
                }


def homepage(request):
    """Get all the details needed for the homepage"""
    context = {}
    for name, value in Homepage().get_cached_values():
        context[name] = value()
    return render(request, 'homepage.html', context)


@user_passes_test(lambda u: u.is_staff)
def reset_homepage_cache(request):
    """Reset the homepage cache"""
    # pylint: disable=unused-argument

    template_keys = (
            'homepage_top',
            'homepage_bottom',
            'dropdown_recent_articles',
            )
    for key in template_keys:
        cache.delete(make_template_fragment_key(key))

    return redirect('index')


class StripeFormMixin(object):
    """Prefills the StripeForm values."""
    def get_initial(self):
        """Add initial data to the form."""
        initial = super(StripeFormMixin, self).get_initial()
        initial['stripe_pk'] = settings.STRIPE_PUB_KEY
        initial['stripe_label'] = 'Buy'
        initial['stripe_description'] = ''
        initial['stripe_fee'] = 0
        initial['stripe_bitcoin'] = True
        return initial


class DonationFormView(StripeFormMixin, FormView):
    """Accepts donations from all users."""
    form_class = StripeForm
    template_name = 'forms/donate.html'

    def get_initial(self):
        """Adds the user's email to the form if they're logged in."""
        user = self.request.user
        email = ''
        if user.is_authenticated():
            email = user.email
        return {
            'stripe_email': email,
            'stripe_label': 'Donate',
            'stripe_description': 'Tax Deductible Donation'
        }

    def form_valid(self, form):
        """If the form is valid, charge the token provided by the form, then send a receipt."""
        token = form.cleaned_data['stripe_token']
        email = form.cleaned_data['stripe_email']
        amount = form.cleaned_data['stripe_amount']
        type_ = form.cleaned_data['type']
        if type_ == 'one-time':
            charge = self.make_charge(token, amount, email)
            if charge is None:
                return self.form_invalid(form)
            # Send the receipt
            send_charge_receipt.delay(charge.id)
        elif type_ == 'monthly':
            subscription = self.make_subscription(token, amount, email)
            if subscription is None:
                return self.form_invalid(form)
        return super(DonationFormView, self).form_valid(form)

    def get_success_url(self):
        """Return a redirection the donation page, always."""
        return reverse('donate-thanks')

    def make_charge(self, token, amount, email):
        """Make a Stripe charge and catch any errors."""
        charge = None
        error_msg = None
        try:
            charge = stripe_retry_on_error(
                    stripe.Charge.create,
                    amount=amount,
                    currency='usd',
                    source=token,
                    description='Donation from %s' % email,
                    metadata={
                        'email': email,
                        'action': 'donation'
                        },
                    idempotency_key=True,
                    )
        except stripe.error.CardError:
            # card declined
            logger.warn('Card was declined.')
            error_msg = 'Your card was declined'
        except (
                stripe.error.InvalidRequestError,
                # Invalid parameters were supplied to Stripe's API
                stripe.error.AuthenticationError,
                # Authentication with Stripe's API failed
                stripe.error.APIConnectionError,
                # Network communication with Stripe failed
                stripe.error.StripeError,
                # Generic error
                ) as exception:
            logger.error(exception, exc_info=sys.exc_info())
            error_msg = ('Oops, something went wrong on our end.'
                        ' Sorry about that!')
        finally:
            if error_msg:
                messages.error(self.request, error_msg)
            else:
                self.request.session['donated'] = amount
                self.request.session['ga'] = 'donation'
        return charge

    def make_subscription(self, token, amount, email):
        """Start a subscription for recurring donations"""
        quantity = amount / 100
        if self.request.user.is_authenticated:
            user = self.request.user
            customer = self.request.user.profile.customer()
        else:
            user = None
            customer = stripe_retry_on_error(
                    stripe.Customer.create,
                    description='Donation for {}'.format(email),
                    email=email,
                    idempotency_key=True,
                    )
        try:
            subscription = stripe_retry_on_error(
                    customer.subscriptions.create,
                    plan='donate',
                    source=token,
                    quantity=quantity,
                    idempotency_key=True,
                    )
        except stripe.error.CardError:
            logger.warn('Card was declined.')
            messages.error(self.request, 'Your card was declined')
        except stripe.error.StripeError as exception:
            logger.error(exception, exc_info=sys.exc_info())
            messages.error(
                    self.request,
                    'Oops, something went wrong on our end. Sorry about that!',
                    )
        else:
            RecurringDonation.objects.create(
                    user=user,
                    email=email,
                    amount=quantity,
                    customer_id=customer.id,
                    subscription_id=subscription.id,
                    )
        return subscription


class DonationThanksView(TemplateView):
    """Returns a thank you message to the user."""
    template_name = 'forms/donate_thanks.html'


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
    return render(request, '500.html', status=500)


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
