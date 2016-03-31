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
from django.db.models import Sum, FieldDoesNotExist
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.utils.decorators import method_decorator
from django.views.generic import View, ListView

from muckrock.agency.models import Agency
from muckrock.foia.models import FOIARequest, FOIAFile
from muckrock.forms import MRFilterForm, NewsletterSignupForm
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.news.models import Article
from muckrock.project.models import Project
from muckrock.utils import cache_get_or_set

import logging
import re
import requests
from haystack.views import SearchView
from haystack.query import RelatedSearchQuerySet

class MRFilterableListView(ListView):
    """
    The main feature of MRFilterableListView is the ability to filter
    a set of request objects by a dynamic dictionary of filters and
    lookup conditions. MRFilterableListView should be used in conjunction
    with MRFilterForm, available in the `muckrock.forms` module.

    To see an example of a subclass of MRFilterableListView that adds new
    filter fields, look at `muckrock.foia.views.RequestList`.
    """

    title = ''
    template_name = 'lists/base_list.html'
    default_sort = 'title'
    default_order = 'asc'

    def get_filters(self):
        """
        Filters should be the same as the fields in MRFilterForm, or whichever
        subclass of MRFilterForm is being used in as this class's `filter_form`.
        Filters are an array of key-value pairs.
        Required pairs are the field name and the [lookup condition][a].

        [a]: https://docs.djangoproject.com/en/1.7/ref/models/querysets/#field-lookups
        """
        # pylint: disable=no-self-use
        return [
            {
                'field': 'user',
                'lookup': 'exact',
            },
            {
                'field': 'agency',
                'lookup': 'exact',
            },
            {
                'field': 'jurisdiction',
                'lookup': 'exact',
            },
            {
                'field': 'tags',
                'lookup': 'name__in',
            },
        ]

    def clean_filter_value(self, filter_key, filter_value):
        """Cleans filter inputs to their expected values if detected as incorrect"""
        # pylint:disable=no-self-use
        # pylint:disable=too-many-branches
        if not filter_value:
            return None

        # tags need to be parsed into an array before filtering
        if filter_key == 'tags':
            filter_value = filter_value.split(',')
        if filter_key == 'user':
            # if looking up by PK, then result will be empty
            # if looking up by username, then result will have length
            if len(re.findall(r'\D+', filter_value)) > 0:
                try:
                    filter_value = User.objects.get(username=filter_value).pk
                except User.DoesNotExist:
                    filter_value = None
                # username is unique so only one result should be returned by get
        if filter_key == 'agency':
            if len(re.findall(r'\D+', filter_value)) > 0:
                try:
                    filter_value = Agency.objects.get(slug=filter_value).pk
                except Agency.DoesNotExist:
                    filter_value = None
                except Agency.MultipleObjectsReturned:
                    filter_value = Agency.objects.filter(slug=filter_value)[0]
        if filter_key == 'jurisdiction':
            if len(re.findall(r'\D+', filter_value)) > 0:
                try:
                    filter_value = Jurisdiction.objects.get(slug=filter_value).pk
                except Jurisdiction.DoesNotExist:
                    filter_value = None
                except Jurisdiction.MultipleObjectsReturned:
                    filter_value = Jurisdiction.objects.filter(slug=filter_value)[0]

        return filter_value

    def get_filter_data(self):
        """Returns a list of filter values and a url query for the filter."""
        get = self.request.GET
        filter_initials = {}
        filter_url = ''
        for filter_by in self.get_filters():
            filter_key = filter_by['field']
            filter_value = get.get(filter_key, None)
            filter_value = self.clean_filter_value(filter_key, filter_value)
            if filter_value:
                if isinstance(filter_value, list):
                    try:
                        filter_value = ', '.join(filter_value)
                    except TypeError:
                        filter_value = str(filter_value)
                kwarg = {filter_key: filter_value}
                try:
                    filter_initials.update(kwarg)
                    filter_url += '&' + str(filter_key) + '=' + str(filter_value)
                except ValueError:
                    pass
        return {
            'filter_initials': filter_initials,
            'filter_url': filter_url
        }

    def filter_list(self, objects):
        """Filters a list of objects"""
        get = self.request.GET
        kwargs = {}
        for filter_by in self.get_filters():
            filter_key = filter_by['field']
            filter_lookup = filter_by['lookup']
            filter_value = get.get(filter_key, None)
            filter_value = self.clean_filter_value(filter_key, filter_value)
            if filter_value:
                kwargs.update({'{0}__{1}'.format(filter_key, filter_lookup): filter_value})
        # tag filtering could add duplicate items to results, so .distinct()
        # is used only if there are tags, as adding distinct can cause
        # performance issues
        if get.get('tags'):
            objects = objects.distinct()
        try:
            objects = objects.filter(**kwargs)
        except FieldError:
            pass
        except ValueError:
            error_msg = "Sorry, there was a problem with your filters. Please try filtering again."
            messages.error(self.request, error_msg)
        return objects

    def sort_list(self, objects):
        """Sorts the list of objects"""
        sort = self.request.GET.get('sort', self.default_sort)
        order = self.request.GET.get('order', self.default_order)
        # We need to make sure the field to sort by actually exists.
        # If the field doesn't exist, revert to the default field.
        # Otherwise, Django will throw a hard-to-catch FieldError.
        # It's hard to catch because the error isn't raised until
        # the QuerySet is evaluated. <Insert poop emoji here>
        try:
            # pylint:disable=protected-access
            self.get_model()._meta.get_field_by_name(sort)
            # pylint:enable=protected-access
        except FieldDoesNotExist:
            sort = self.default_sort
        if order != 'asc':
            sort = '-' + sort
        objects = objects.order_by(sort)
        return objects

    def get_context_data(self, **kwargs):
        """Gets basic context, including title, form, and url"""
        context = super(MRFilterableListView, self).get_context_data(**kwargs)
        filter_data = self.get_filter_data()
        context['title'] = self.title
        context['per_page'] = int(self.get_paginate_by(context['object_list']))
        try:
            context['filter_form'] = MRFilterForm(initial=filter_data['filter_initials'])
        except ValueError:
            context['filter_form'] = MRFilterForm()
        context['filter_url'] = filter_data['filter_url']
        context['active_sort'] = self.request.GET.get('sort', self.default_sort)
        context['active_order'] = self.request.GET.get('order', self.default_order)
        return context

    def get_queryset(self):
        objects = super(MRFilterableListView, self).get_queryset()
        objects = self.filter_list(objects)
        objects = self.sort_list(objects)
        return objects

    def get_paginate_by(self, queryset):
        """Paginates list by the return value"""
        try:
            per_page = int(self.request.GET.get('per_page'))
            return max(min(per_page, 100), 5)
        except (ValueError, TypeError):
            return 25

    def get_model(self):
        """Get the model for this view - directly or from the queryset"""
        if self.queryset is not None:
            return self.queryset.model
        if self.model is not None:
            return self.model


class MRSearchView(SearchView):
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

    def get_paginate_by(self):
        """Gets per_page the right way"""
        try:
            per_page = int(self.request.GET.get('per_page'))
            return max(min(per_page, 100), 5)
        except (ValueError, TypeError):
            return 25

    def build_page(self):
        """Circumvents the hard-coded haystack per page value."""
        self.results_per_page = self.get_paginate_by()
        return super(MRSearchView, self).build_page()


class NewsletterSignupView(View):
    """Allows users to signup for our MailChimp newsletter."""
    def get(self, request, *args, **kwargs):
        """Returns a signup form"""
        template = 'forms/newsletter/signup.html'
        context = {'form': NewsletterSignupForm(initial={'list': settings.MAILCHIMP_LIST_DEFAULT})}
        return render_to_response(template, context, context_instance=RequestContext(request))

    def post(self, request, *args, **kwargs):
        """If given email address data, adds that email to our newsletter list.
        Then it returns a thank you for signing up page. If no email is provided or
        the email is already on the list, we return the newsletter signup form again."""
        template = 'forms/newsletter/done.html'
        signup_form = NewsletterSignupForm(request.POST)
        context = {}
        try:
            if signup_form.is_valid():
                # take the cleaned email and add it to our mailing list
                _email = signup_form.cleaned_data['email']
                _list = signup_form.cleaned_data['list']
                self.subscribe(_email, _list)
                messages.success(request, ('Thank you for subscribing to our newsletter. '
                                           'We sent a confirmation email to your inbox.'))
                return redirect('index')
            else:
                raise ValueError('The form data is invalid.')
        except (ValueError, requests.exceptions.HTTPError) as exception:
            messages.error(request, 'Sorry, there was a problem subscribing you to the list.')
            logging.error(exception)
            template = 'forms/newsletter/signup.html'
            context = {'form': signup_form}
        return render_to_response(template, context, context_instance=RequestContext(request))

    def subscribe(self, _email, _list):
        """Adds the email to the mailing list throught the MailChimp API.
        http://developer.mailchimp.com/documentation/mailchimp/reference/lists/members/"""
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
        response.raise_for_status()
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
                                   [:3],
            600)
    try:
        lead_article = articles[0]
        other_articles = articles[1:]
    except IndexError:
        # no published articles
        lead_article = None
        other_articles = None
    featured_projects = cache_get_or_set(
            'hp:featured_projects',
            lambda: Project.objects.get_public().filter(featured=True)[:4],
            600)
    federal_government = cache_get_or_set(
            'hp:federal_government',
            lambda: Jurisdiction.objects.filter(level='f').first(),
            None)
    completed_requests = cache_get_or_set(
            'hp:completed_requests',
            lambda: (FOIARequest.objects.get_public().get_done()
                   .order_by('-date_done')
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

@user_passes_test(lambda u: u.is_staff)
def reset_homepage_cache(request):
    """Reset the homepage cache"""
    # pylint: disable=unused-argument
    key = make_template_fragment_key('homepage')
    cache.delete(key)
    cache.set('hp:articles',
            Article.objects.get_published().prefetch_related(
                'authors',
                'authors__profile',
                'projects')[:3],
            600)
    cache.set('hp:featured_projects',
            Project.objects.get_public().filter(featured=True)[:4],
            600)
    cache.set('hp:federal_government',
            Jurisdiction.objects.filter(level='f').first(),
            None)
    cache.set('hp:completed_requests',
            FOIARequest.objects.get_public().get_done()
                   .order_by('-date_done')
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
