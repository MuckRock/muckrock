"""
Views to display lists of FOIA requests
"""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.postgres.aggregates.general import StringAgg
from django.core.urlresolvers import reverse
from django.db.models import Count, F
from django.http import Http404, StreamingHttpResponse
from django.shortcuts import redirect
from django.views.generic import TemplateView

from actstream.models import following
from furl import furl
from itertools import chain
import unicodecsv as csv

from muckrock.agency.models import Agency
from muckrock.foia.filters import (
    FOIARequestFilterSet,
    MyFOIARequestFilterSet,
    MyFOIAMultiRequestFilterSet,
    ProcessingFOIARequestFilterSet,
    AgencyFOIARequestFilterSet,
)
from muckrock.foia.models import (
    FOIARequest,
    FOIAMultiRequest,
    )
from muckrock.models import ExtractDay, Now
from muckrock.news.models import Article
from muckrock.project.models import Project
from muckrock.utils import Echo
from muckrock.views import (
        class_view_decorator,
        MRFilterListView,
        MRSearchFilterListView,
        )


class RequestExploreView(TemplateView):
    """Provides a top-level page for exploring interesting requests."""
    template_name = 'foia/explore.html'

    def get_context_data(self, **kwargs):
        """Adds interesting data to the context for rendering."""
        context = super(RequestExploreView, self).get_context_data(**kwargs)
        user = self.request.user
        visible_requests = FOIARequest.objects.get_viewable(user)
        context['top_agencies'] = (
            Agency.objects
            .get_approved()
            .annotate(foia_count=Count('foiarequest'))
            .order_by('-foia_count')
        )[:9]
        context['featured_requests'] = (
            visible_requests
            .filter(featured=True)
            .order_by('featured')
            .select_related_view()
        )
        context['recent_news'] = (
            Article.objects
            .get_published()
            .annotate(foia_count=Count('foias'))
            .exclude(foia_count__lt=2)
            .exclude(foia_count__gt=9)
            .prefetch_related(
                'authors',
                'foias',
                'foias__user',
                'foias__user__profile',
                'foias__agency',
                'foias__agency__jurisdiction',
                'foias__jurisdiction__parent__parent')
            .order_by('-pub_date')
        )[:3]
        context['featured_projects'] = (
            Project.objects
            .get_visible(user)
            .filter(featured=True)
            .prefetch_related(
                'requests',
                'requests__user',
                'requests__user__profile',
                'requests__agency',
                'requests__agency__jurisdiction',
                'requests__jurisdiction__parent__parent')
        )
        context['recently_completed'] = (
            visible_requests
            .get_done()
            .order_by('-date_done', 'pk')
            .select_related_view()
            .get_public_file_count(limit=5))
        context['recently_rejected'] = (
            visible_requests
            .filter(status__in=['rejected', 'no_docs'])
            .order_by('-date_updated', 'pk')
            .select_related_view()
            .get_public_file_count(limit=5))
        return context


class RequestList(MRSearchFilterListView):
    """Base list view for other list views to inherit from"""
    model = FOIARequest
    filter_class = FOIARequestFilterSet
    title = 'All Requests'
    template_name = 'foia/list.html'
    default_sort = 'date_updated'
    default_order = 'desc'
    sort_map = {
            'title': 'title',
            'user': 'user__first_name',
            'agency': 'agency__name',
            'date_updated': 'date_updated',
            'date_submitted': 'date_submitted',
            }

    def get_queryset(self):
        """Limits requests to those visible by current user"""
        objects = super(RequestList, self).get_queryset()
        objects = objects.select_related_view()
        return objects.get_viewable(self.request.user)

    def get_context_data(self):
        """Add download link for downloading csv"""
        context = super(RequestList, self).get_context_data()
        url = furl(self.request.get_full_path())
        url.args['content_type'] = 'csv'
        context['csv_link'] = url.url
        return context

    def render_to_response(self, context, **kwargs):
        """Allow CSV responses"""

        wants_csv = self.request.GET.get('content_type') == 'csv'
        has_perm = self.request.user.has_perm('foia.export_csv')
        if wants_csv and has_perm:
            psuedo_buffer = Echo()
            fields = (
                    (lambda f: f.user.username, 'User'),
                    (lambda f: f.title, 'Title'),
                    (lambda f: f.get_status_display(), 'Status'),
                    (lambda f: settings.MUCKROCK_URL + f.get_absolute_url(), 'URL'),
                    (lambda f: f.jurisdiction.name, 'Jurisdiction'),
                    (lambda f: f.jurisdiction.pk, 'Jurisdiction ID'),
                    (lambda f: f.agency.name if f.agency else '', 'Agency'),
                    (lambda f: f.agency.pk if f.agency else '', 'Agency ID'),
                    (lambda f: f.date_followup, 'Followup Date'),
                    (lambda f: f.date_estimate, 'Estimated Completion Date'),
                    (lambda f: f.description, 'Description'),
                    (lambda f: f.tracking_id, 'Tracking Number'),
                    (lambda f: f.embargo, 'Embargo'),
                    (lambda f: f.days_since_submitted, 'Days since submitted'),
                    (lambda f: f.days_since_updated, 'Days since updated'),
                    (lambda f: f.project_names, 'Projects'),
                    (lambda f: f.tag_names, 'Tags'),
                    )
            foias = (context['paginator'].object_list
                    .select_related(None)
                    .select_related(
                        'user',
                        'jurisdiction',
                        'agency',
                        )
                    .only(
                        'user__username',
                        'title',
                        'status',
                        'slug',
                        'jurisdiction__name',
                        'jurisdiction__slug',
                        'jurisdiction__id',
                        'agency__name',
                        'agency__id',
                        'date_followup',
                        'date_estimate',
                        'description',
                        'tracking_id',
                        'embargo',
                        )
                    .annotate(
                        days_since_submitted=ExtractDay(Now() - F('date_submitted')),
                        days_since_updated=ExtractDay(Now() - F('date_updated')),
                        project_names=StringAgg('projects__title', ',', distinct=True),
                        tag_names=StringAgg('tags__name', ',', distinct=True),
                        )
                    )
            writer = csv.writer(psuedo_buffer)
            response = StreamingHttpResponse(
                    chain(
                        [writer.writerow(f[1] for f in fields)],
                        (writer.writerow(f[0](foia) for f in fields) for foia in foias),
                        ),
                    content_type='text/csv',
                    )
            response['Content-Disposition'] = 'attachment; filename="requests.csv"'
            return response
        else:
            return super(RequestList, self).render_to_response(context, **kwargs)


@class_view_decorator(login_required)
class MyRequestList(RequestList):
    """View requests owned by current user"""
    filter_class = MyFOIARequestFilterSet
    title = 'Your Requests'
    template_name = 'foia/my_list.html'

    def get_queryset(self):
        """Limit to just requests owned by the current user."""
        queryset = super(MyRequestList, self).get_queryset()
        return queryset.filter(user=self.request.user)


@class_view_decorator(user_passes_test(
    lambda u: u.is_authenticated and u.profile.acct_type == 'agency'))
class AgencyRequestList(RequestList):
    """View requests owned by current agency"""
    filter_class = AgencyFOIARequestFilterSet
    title = "Your Agency's Requests"
    template_name = 'foia/agency_list.html'

    def get_queryset(self):
        """Requests owned by the current agency that they can respond to."""
        queryset = super(AgencyRequestList, self).get_queryset()
        return queryset.filter(
                agency=self.request.user.profile.agency,
                status__in=(
                    'ack',
                    'processed',
                    'appealing',
                    'fix',
                    'payment',
                    'partial',
                    ),
                )


@class_view_decorator(login_required)
class MyMultiRequestList(MRFilterListView):
    """View requests owned by current user"""
    model = FOIAMultiRequest
    filter_class = MyFOIAMultiRequestFilterSet
    title = 'Multirequests'
    template_name = 'foia/multirequest_list.html'

    def dispatch(self, *args, **kwargs):
        """Basic users cannot access this view"""
        if self.request.user.is_authenticated and not self.request.user.profile.is_advanced():
            err_msg = (
                'Multirequests are a pro feature. '
                '<a href="%(settings_url)s">Upgrade today!</a>' % {
                    'settings_url': reverse('accounts')
                }
            )
            messages.error(self.request, err_msg)
            return redirect('foia-mylist')
        return super(MyMultiRequestList, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        """Limit to just requests owned by the current user."""
        queryset = super(MyMultiRequestList, self).get_queryset()
        return queryset.filter(user=self.request.user)


@class_view_decorator(login_required)
class FollowingRequestList(RequestList):
    """List of all FOIA requests the user is following"""
    title = 'Requests You Follow'

    def get_queryset(self):
        """Limits FOIAs to those followed by the current user"""
        queryset = super(FollowingRequestList, self).get_queryset()
        followed = [f.pk for f in following(self.request.user, FOIARequest)
                if f is not None]
        return queryset.filter(pk__in=followed)


class ProcessingRequestList(RequestList):
    """List all of the currently processing FOIA requests."""
    title = 'Processing Requests'
    filter_class = ProcessingFOIARequestFilterSet
    template_name = 'foia/processing_list.html'
    default_sort = 'date_processing'
    default_order = 'asc'
    sort_map = {
            'title': 'title',
            'date_submitted': 'date_submitted',
            'date_processing': 'date_processing',
            }

    def dispatch(self, *args, **kwargs):
        """Only staff can see the list of processing requests."""
        if not self.request.user.is_staff:
            raise Http404()
        return super(ProcessingRequestList, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        """Apply select and prefetch related"""
        objects = super(ProcessingRequestList, self).get_queryset()
        return objects.prefetch_related('communications').filter(status='submitted')
