"""
Views for muckrock project
"""
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import FieldError
from django.core.paginator import Paginator, InvalidPage
from django.db.models import Sum
from django.http import HttpResponseServerError, Http404
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext, Context, loader
from django.utils.decorators import method_decorator
from django.views.generic.list import ListView

from muckrock.agency.models import Agency
from muckrock.foia.models import FOIARequest, FOIAFile
from muckrock.forms import MRFilterForm
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.news.models import Article

import re
from haystack.views import SearchView

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
        # tag filtering could add duplicate items to results, so .distinct() is used
        try:
            objects = objects.filter(**kwargs).distinct()
        except FieldError:
            pass
        except ValueError:
            error_msg = "Sorry, there was a problem with your filters. Please try filtering again."
            messages.error(self.request, error_msg)
        return objects

    def sort_list(self, objects):
        """Sorts the list of objects"""
        get = self.request.GET
        sort = get.get('sort')
        if sort in ['title', 'status', 'date_submitted']:
            order = get.get('order', 'asc')
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
        return context

    def get_queryset(self):
        objects = super(MRFilterableListView, self).get_queryset()
        objects = self.sort_list(objects)
        return self.filter_list(objects)

    def get_paginate_by(self, queryset):
        """Paginates list by the return value"""
        try:
            per_page = int(self.request.GET.get('per_page'))
            return min(per_page, 100)
        except (ValueError, TypeError):
            return 25


class MRSearchView(SearchView):
    """Always lower case queries for case insensitive searches"""

    def get_query(self):
        """Lower case the query"""
        return super(MRSearchView, self).get_query().lower()

    def extra_context(self):
        """Adds per_page to context data"""
        context = super(MRSearchView, self).extra_context()
        context['per_page'] = int(self.request.GET.get('per_page', 25))
        return context

    def get_paginate_by(self):
        """Gets per_page the right way"""
        return int(self.request.GET.get('per_page', 25))

    def build_page(self):
        """Circumvents the hard-coded haystack per page value."""
        # pylint: disable=pointless-statement
        # disabled pylint because this is not really my code
        # also, this should only be temporary (see issue #383)
        try:
            page_no = int(self.request.GET.get('page', 1))
        except (TypeError, ValueError):
            raise Http404("Not a valid number for page.")

        if page_no < 1:
            raise Http404("Pages should be 1 or greater.")

        start_offset = (page_no - 1) * self.results_per_page
        self.results[start_offset:start_offset + self.results_per_page]

        paginator = Paginator(self.results, self.get_paginate_by())
        try:
            page = paginator.page(page_no)
        except InvalidPage:
            raise Http404("No such page!")
        return (paginator, page)

def front_page(request):
    """Get all the details needed for the front page"""
    # pylint: disable=unused-variable
    # pylint: disable=E1103

    try:
        articles = Article.objects.get_published()[:1]
    except IndexError:
        # no published articles
        articles = None

    public_reqs = FOIARequest.objects.get_public()
    featured_reqs = public_reqs.filter(featured=True).order_by('-date_done')[:3]

    num_requests = FOIARequest.objects.exclude(status='started').count()
    num_completed_requests = FOIARequest.objects.filter(status='done').count()
    num_denied_requests = FOIARequest.objects.filter(status='rejected').count()
    num_pages = FOIAFile.objects.aggregate(Sum('pages'))['pages__sum']

    most_viewed_reqs = FOIARequest.objects.order_by('-times_viewed')[:5]
    overdue_requests = FOIARequest.objects.get_overdue().get_public()[:5]

    return render_to_response('front_page.html', locals(),
                              context_instance=RequestContext(request))

def blog(request, path=''):
    """Redirect to the new blog URL"""
    # pylint: disable=unused-argument
    return redirect('http://blog.muckrock.com/%s/' % path, permanant=True)

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
    500 error handler which includes ``request`` in the context.

    Templates: `500.html`
    Context: None
    """

    template = loader.get_template('500.html')
    return HttpResponseServerError(template.render(Context({'request': request})))


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
