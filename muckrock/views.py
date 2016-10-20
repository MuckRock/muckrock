"""
Views for muckrock project
"""
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.core.exceptions import FieldError
from django.core.urlresolvers import reverse
from django.db.models import Sum, FieldDoesNotExist
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.utils.decorators import method_decorator
from django.utils.html import escape
from django.views.generic import View, ListView, FormView, TemplateView

from muckrock.agency.models import Agency
from muckrock.foia.models import FOIARequest, FOIAFile
from muckrock.forms import MRFilterForm, NewsletterSignupForm, StripeForm
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.message.tasks import send_charge_receipt
from muckrock.news.models import Article
from muckrock.project.models import Project
from muckrock.utils import cache_get_or_set

import logging
import re
import requests
from haystack.views import SearchView
from haystack.query import RelatedSearchQuerySet
import stripe

logger = logging.getLogger(__name__)


class OrderedSortMixin(object):
    """Sorts and orders a queryset given some inputs."""
    default_sort = 'id'
    default_order = 'asc'

    def sort_queryset(self, queryset):
        """
        Sorts a queryset of objects.

        We need to make sure the field to sort by actually exists.
        If the field doesn't exist, return the unordered queryset.
        """
        # pylint:disable=protected-access
        sort = self.request.GET.get('sort', self.default_sort)
        order = self.request.GET.get('order', self.default_order)
        try:
            queryset.model._meta.get_field(sort)
        except FieldDoesNotExist:
            sort = self.default_sort
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


class FilterMixin(object):
    """
    The FilterMixin gives the ability to filter a list
    of objects with the help of the django_filters library.

    It requires a filter_class be defined.
    """
    filter_class = None

    def get_filter(self):
        """Returns the filter, if a filter_class is defined. If it isn't, an error is raised."""
        if self.filter_class is None:
            raise AttributeError('Missing a filter class.')
        return self.filter_class(self.request.GET, queryset=self.get_queryset())

    def get_context_data(self, **kwargs):
        """
        Adds the filter to the context and overrides the
        object_list value with the filter's queryset.
        We also apply pagination to the filter queryset.
        """
        context = super(FilterMixin, self).get_context_data(**kwargs)
        _filter = self.get_filter()
        queryset = _filter.qs
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


class MRFilterableListView(PaginationMixin, OrderedSortMixin, FilterMixin, ListView):
    """Allows for list views that are filterable and orderable."""
    title = ''
    template_name = 'base_list.html'

    def get_context_data(self, **kwargs):
        """Adds title to the context data."""
        context = super(MRFilterableListView, self).get_context_data(**kwargs)
        context['title'] = self.title
        return context


class MRSearchView(PaginationMixin, SearchView):
    """Always lower case queries for case insensitive searches"""

    def __init__(self, *args, **kwargs):
        kwargs['searchqueryset'] = RelatedSearchQuerySet()
        super(MRSearchView, self).__init__(*args, **kwargs)

    def get_query(self):
        """Lower case the query"""
        return super(MRSearchView, self).get_query().lower()

    def get_results(self):
        """Apply select related to results"""
        results = super(MRSearchView, self).get_results()
        try:
            results = results.load_all_queryset(
                FOIARequest, FOIARequest.objects.select_related('jurisdiction'))
        except AttributeError:
            pass

        return results

    def extra_context(self):
        """Adds per_page to context data"""
        # pylint: disable=not-callable
        context = super(MRSearchView, self).extra_context()
        context['per_page'] = int(self.request.GET.get('per_page', 25))
        models = self.request.GET.getlist('models')
        context['news_checked'] = 'news.article' in models
        context['foia_checked'] = 'foia.foiarequest' in models
        context['qanda_checked'] = 'qanda.question' in models
        return context

    def build_page(self):
        """Circumvents the hard-coded haystack per page value."""
        self.results_per_page = self.get_paginate_by()
        return super(MRSearchView, self).build_page()


class NewsletterSignupView(View):
    """Allows users to signup for our MailChimp newsletter."""
    def get(self, request, *args, **kwargs):
        """Returns a signup form"""
        template = 'forms/newsletter.html'
        context = {'form': NewsletterSignupForm(initial={'list': settings.MAILCHIMP_LIST_DEFAULT})}
        return render_to_response(template, context, context_instance=RequestContext(request))

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
        response = requests.post(api_url, json=data, headers=headers)
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

def homepage(request):
    """Get all the details needed for the homepage"""
    # pylint: disable=unused-variable
    articles = cache_get_or_set(
            'hp:articles',
            lambda: Article.objects.get_published()
                                   .prefetch_related(
                                        'authors',
                                        'authors__profile',
                                        'projects',
                                    )
                                   [:7],
            600)
    featured_projects = cache_get_or_set(
            'hp:featured_projects',
            lambda: Project.objects.get_public().filter(featured=True)[:4],
            600)
    completed_requests = cache_get_or_set(
            'hp:completed_requests',
            lambda: (FOIARequest.objects.get_public().get_done()
                   .order_by('-date_done', 'pk')
                   .select_related_view()
                   .get_public_file_count(limit=6)),
            600)
    stats = cache_get_or_set(
            'hp:stats',
            lambda: {
                'request_count': FOIARequest.objects
                    .exclude(status='started').count(),
                'completed_count': FOIARequest.objects.get_done().count(),
                'page_count': FOIAFile.objects
                    .aggregate(Sum('pages'))['pages__sum'],
                'agency_count': Agency.objects.get_approved().count()
            },
            600)
    return render_to_response('homepage.html', locals(),
                              context_instance=RequestContext(request))


class LandingView(TemplateView):
    """Renders the landing page template."""
    template_name = 'flatpages/landing.html'


@user_passes_test(lambda u: u.is_staff)
def reset_homepage_cache(request):
    """Reset the homepage cache"""
    # pylint: disable=unused-argument

    cache.delete(make_template_fragment_key('news'))
    cache.delete(make_template_fragment_key('projects'))
    cache.delete(make_template_fragment_key('recent_articles'))

    cache.set('hp:articles',
            Article.objects.get_published().prefetch_related(
                'authors',
                'authors__profile',
                'projects')[:3],
            600)
    cache.set('hp:featured_projects',
            Project.objects.get_public().filter(featured=True)[:4],
            600)
    cache.set('hp:completed_requests',
            FOIARequest.objects.get_public().get_done()
                   .order_by('-date_done', 'pk')
                   .select_related_view()
                   .get_public_file_count(limit=6),
            600)
    cache.set('hp:stats',
            {
                'request_count': FOIARequest.objects
                    .exclude(status='started').count(),
                'completed_count': FOIARequest.objects.get_done().count(),
                'page_count': FOIAFile.objects
                    .aggregate(Sum('pages'))['pages__sum'],
                'agency_count': Agency.objects.get_approved().count()
            },
            600)
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
        charge = self.make_charge(token, amount, email)
        if charge is None:
            return self.form_invalid(form)
        # Send the receipt
        send_charge_receipt.delay(charge.id)
        return super(DonationFormView, self).form_valid(form)

    def get_success_url(self):
        """Return a redirection the donation page, always."""
        return reverse('donate-thanks')

    def make_charge(self, token, amount, email):
        """Make a Stripe charge and catch any errors."""
        charge = None
        error_msg = None
        try:
            charge = stripe.Charge.create(
                amount=amount,
                currency='usd',
                source=token,
                description='Donation from %s' % email,
                metadata={
                    'email': email,
                    'action': 'donation'
                }
            )
        except stripe.error.InvalidRequestError as exception:
            # Invalid parameters were supplied to Stripe's API
            logger.error(exception)
            error_msg = ('Oops, something went wrong on our end.'
                        ' Sorry about that!')
        except stripe.error.AuthenticationError as exception:
            # Authentication with Stripe's API failed
            logger.error(exception)
            error_msg = ('Oops, something went wrong on our end.'
                        ' Sorry about that!')
        except stripe.error.APIConnectionError as exception:
            # Network communication with Stripe failed
            logger.error(exception)
            error_msg = ('Oops, something went wrong on our end.'
                        ' Sorry about that!')
        except stripe.error.StripeError as exception:
            # Generic error
            logger.error(exception)
            error_msg = ('Oops, something went wrong on our end.'
                        ' Sorry about that!')
        finally:
            if error_msg:
                self.request.session['donated'] = False
                messages.error(self.request, error_msg)
            else:
                self.request.session['donated'] = True
                self.request.session['ga'] = 'donation'
        return charge


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
    response = render_to_response('500.html', {}, context_instance=RequestContext(request))
    response.status_code = 500
    return response

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
