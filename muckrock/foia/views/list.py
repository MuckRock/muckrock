"""
Views to display lists of FOIA requests
"""

# Django
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.postgres.aggregates.general import StringAgg
from django.core.urlresolvers import reverse
from django.db.models import Count, DurationField, F, Prefetch
from django.db.models.functions import Cast, Now
from django.http import Http404, StreamingHttpResponse
from django.shortcuts import redirect
from django.views.generic import TemplateView

# Standard Library
from datetime import date, timedelta
from itertools import chain

# Third Party
import actstream
import unicodecsv as csv
from actstream.models import following
from furl import furl

# MuckRock
from muckrock.agency.models import Agency
from muckrock.crowdsource.forms import CrowdsourceChoiceForm
from muckrock.foia.filters import (
    AgencyFOIARequestFilterSet,
    FOIARequestFilterSet,
    MyFOIARequestFilterSet,
    ProcessingFOIARequestFilterSet,
)
from muckrock.foia.forms import (
    FOIAAccessForm,
    SaveSearchForm,
    SaveSearchFormHandler,
)
from muckrock.foia.models import (
    END_STATUS,
    FOIAComposer,
    FOIARequest,
    FOIASavedSearch,
)
from muckrock.foia.rules import can_embargo, can_embargo_permananently
from muckrock.forms import TagManagerForm
from muckrock.models import ExtractDay
from muckrock.news.models import Article
from muckrock.project.forms import ProjectManagerForm
from muckrock.project.models import Project
from muckrock.tags.models import Tag, parse_tags
from muckrock.utils import Echo
from muckrock.views import (
    MRListView,
    MRSearchFilterListView,
    class_view_decorator,
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
            Agency.objects.get_approved()
            .annotate(foia_count=Count('foiarequest')).order_by('-foia_count')
        )[:9]
        context['featured_requests'] = (
            visible_requests.filter(featured=True).order_by('featured')
            .select_related_view()
        )
        context['recent_news'] = (
            Article.objects.get_published()
            .annotate(foia_count=Count('foias')).exclude(foia_count__lt=2)
            .exclude(foia_count__gt=9).prefetch_related(
                'authors',
                Prefetch(
                    'foias',
                    queryset=FOIARequest.objects.select_related(
                        'composer__user',
                        'agency__jurisdiction__parent__parent',
                    ),
                ),
            ).order_by('-pub_date')
        )[:3]
        context['featured_projects'] = (
            Project.objects.get_visible(user).filter(featured=True)
            .prefetch_related(
                Prefetch(
                    'requests',
                    queryset=FOIARequest.objects.select_related(
                        'composer__user',
                        'agency__jurisdiction__parent__parent',
                    ),
                ),
            )
        )
        context['recently_completed'] = (
            visible_requests.get_done().order_by(
                '-datetime_done', 'pk'
            ).select_related_view().get_public_file_count(limit=5)
        )
        context['recently_rejected'] = (
            visible_requests.filter(status__in=['rejected', 'no_docs'])
            .order_by('-datetime_updated', 'pk').select_related_view()
            .get_public_file_count(limit=5)
        )
        return context


class RequestList(MRSearchFilterListView):
    """Base list view for other list views to inherit from"""
    model = FOIARequest
    filter_class = FOIARequestFilterSet
    title = 'All Requests'
    template_name = 'foia/list.html'
    default_sort = 'datetime_updated'
    default_order = 'desc'
    sort_map = {
        'title': 'title',
        'user': 'user__first_name',
        'agency': 'agency__name',
        'date_updated': 'datetime_updated',
        'date_submitted': 'composer__datetime_submitted',
        'date_done': 'datetime_done',
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
        context['save_search_form'] = SaveSearchForm(
            initial={
                'search_title': self.request.GET.get('search_title')
            }
        )
        if self.request.user.is_authenticated:
            context['crowdsource_form'] = CrowdsourceChoiceForm(
                user=self.request.user
            )
        if self.request.user.is_authenticated:
            context['saved_searches'] = (
                FOIASavedSearch.objects.filter(user=self.request.user)
            )
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
                (
                    lambda f: f.jurisdiction.get_level_display(),
                    'Jurisdiction Level',
                ),
                (
                    lambda f: f.jurisdiction.parent.name
                    if f.jurisdiction.level == 'l' else f.jurisdiction.name,
                    'Jurisdiction State',
                ),
                (lambda f: f.agency.name if f.agency else '', 'Agency'),
                (lambda f: f.agency.pk if f.agency else '', 'Agency ID'),
                (lambda f: f.date_followup, 'Followup Date'),
                (lambda f: f.date_estimate, 'Estimated Completion Date'),
                (lambda f: f.composer.requested_docs, 'Requested Documents'),
                (lambda f: f.current_tracking_id(), 'Tracking Number'),
                (lambda f: f.embargo, 'Embargo'),
                (lambda f: f.days_since_submitted, 'Days since submitted'),
                (lambda f: f.days_since_updated, 'Days since updated'),
                (lambda f: f.project_names, 'Projects'),
                (lambda f: f.tag_names, 'Tags'),
            )
            foias = (
                context['paginator'].object_list.select_related(None)
                .select_related(
                    'user',
                    'jurisdiction',
                    'agency',
                    'composer',
                ).prefetch_related(
                    'tracking_ids',
                ).only(
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
                    'embargo',
                    'composer__requested_docs',
                ).annotate(
                    days_since_submitted=ExtractDay(
                        Cast(
                            Now() - F('composer__datetime_submitted'),
                            DurationField()
                        )
                    ),
                    days_since_updated=ExtractDay(
                        Cast(Now() - F('datetime_updated'), DurationField())
                    ),
                    project_names=StringAgg(
                        'projects__title', ',', distinct=True
                    ),
                    tag_names=StringAgg('tags__name', ',', distinct=True),
                )
            )
            writer = csv.writer(psuedo_buffer)
            response = StreamingHttpResponse(
                chain(
                    [writer.writerow(f[1] for f in fields)],
                    (
                        writer.writerow(f[0](foia)
                                        for f in fields)
                        for foia in foias
                    ),
                ),
                content_type='text/csv',
            )
            response['Content-Disposition'
                     ] = 'attachment; filename="requests.csv"'
            return response
        else:
            return super(RequestList,
                         self).render_to_response(context, **kwargs)

    def post(self, request, *args, **kwargs):
        """Allow saving a search/filter"""
        # pylint: disable=unused-argument

        actions = self.get_actions()

        if request.user.is_anonymous:
            messages.error(request, 'Please log in')
            return redirect(request.resolver_match.view_name)

        if 'delete' in request.POST:
            return self._delete(request)

        if request.POST.get('action') == 'save':
            return self._save_search(request)

        try:
            foias = FOIARequest.objects.filter(
                pk__in=request.POST.getlist('foias')
            )
            msg = actions[request.POST['action']](
                foias,
                request.user,
                request.POST,
            )
            if msg:
                messages.success(request, msg)
            return redirect(request.resolver_match.view_name)
        except (KeyError, ValueError):
            if request.POST.get('action') != '':
                messages.error(request, 'Something went wrong')
            return redirect(request.resolver_match.view_name)

    def get_actions(self):
        """Get available actions for this view"""
        return {
            'follow': self._follow,
            'unfollow': self._unfollow,
            'crowdsource': self._crowdsource,
        }

    def _delete(self, request):
        """Delete a saved search"""
        try:
            search = FOIASavedSearch.objects.get(
                pk=request.POST.get('delete'),
                user=request.user,
            )
            search.delete()
            messages.success(request, 'The saved search was deleted')
        except FOIASavedSearch.DoesNotExist:
            messages.error(request, 'That saved search no longer exists')
        return redirect(request.resolver_match.view_name)

    def _save_search(self, request):
        """Save a search"""
        form_handler = SaveSearchFormHandler(request, self.filter_class)
        if form_handler.is_valid():
            search = form_handler.create_saved_search()
            messages.success(request, 'Search saved')
            return redirect(
                '{}?{}'.format(
                    reverse(request.resolver_match.view_name),
                    search.urlencode(),
                )
            )
        else:
            return redirect(request.resolver_match.view_name)

    def _follow(self, foias, user, _post):
        """Follow the selected requests"""
        foias = foias.get_viewable(user)
        for foia in foias:
            actstream.actions.follow(user, foia, actor_only=False)
        return 'Followed requests'

    def _unfollow(self, foias, user, _post):
        """Unfollow the selected requests"""
        foias = foias.get_viewable(user)
        for foia in foias:
            actstream.actions.unfollow(user, foia)
        return 'Unfollowed requests'

    def _crowdsource(self, foias, user, post):
        """Extend the embargo on the selected requests"""
        foias = foias.prefetch_related('communications__files')
        foias = [f for f in foias if f.has_perm(user, 'view')]
        form = CrowdsourceChoiceForm(post, user=user)
        if form.is_valid():
            crowdsource = form.cleaned_data['crowdsource']
            if crowdsource is None:
                return 'No crowdsource selected'
            for foia in foias:
                for comm in foia.communications.all():
                    for file_ in comm.files.all():
                        if file_.doc_id:
                            crowdsource.data.create(
                                url=
                                'https://www.documentcloud.org/documents/{}.html'.
                                format(file_.doc_id)
                            )
        return 'Files added to assignment'

    def get(self, request, *args, **kwargs):
        """Check for loading saved searches"""
        if 'load' in request.GET and request.user.is_authenticated:
            try:
                search = FOIASavedSearch.objects.get(
                    title=request.GET.get('load'),
                    user=request.user,
                )
            except FOIASavedSearch.DoesNotExist:
                return super(RequestList, self).get(request, *args, **kwargs)
            return redirect(
                '{}?{}'.format(
                    reverse(request.resolver_match.view_name),
                    search.urlencode(),
                )
            )
        else:
            return super(RequestList, self).get(request, *args, **kwargs)


@class_view_decorator(login_required)
class MyRequestList(RequestList):
    """View requests owned by current user"""
    filter_class = MyFOIARequestFilterSet
    title = 'Your Requests'
    template_name = 'foia/my_list.html'

    def get_queryset(self):
        """Limit to just requests owned by the current user."""
        queryset = super(MyRequestList, self).get_queryset()
        return queryset.filter(composer__user=self.request.user)

    def get_context_data(self):
        """Add forms for bulk actions"""
        context = super(MyRequestList, self).get_context_data()
        context['project_form'] = ProjectManagerForm(user=self.request.user)
        context['tag_form'] = TagManagerForm(required=False)
        context['share_form'] = FOIAAccessForm(required=False)
        context['can_embargo'] = can_embargo(self.request.user)
        context['can_perm_embargo'] = can_embargo_permananently(
            self.request.user
        )
        return context

    def get_actions(self):
        """Get available actions for this view"""
        actions = super(MyRequestList, self).get_actions()
        actions.update({
            'extend-embargo': self._extend_embargo,
            'remove-embargo': self._remove_embargo,
            'permanent-embargo': self._perm_embargo,
            'project': self._project,
            'tags': self._tags,
            'share': self._share,
            'autofollowup-on': self._autofollowup_on,
            'autofollowup-off': self._autofollowup_off,
        })
        return actions

    def _extend_embargo(self, foias, user, _post):
        """Extend the embargo on the selected requests"""
        end_date = date.today() + timedelta(30)
        foias = [f.pk for f in foias if f.has_perm(user, 'embargo')]
        FOIARequest.objects.filter(pk__in=foias).update(embargo=True)
        # only set date if in end state
        FOIARequest.objects.filter(
            pk__in=foias,
            status__in=END_STATUS,
        ).update(date_embargo=end_date)
        return 'Embargoes extended for 30 days'

    def _remove_embargo(self, foias, user, _post):
        """Remove the embargo on the selected requests"""
        foias = [f.pk for f in foias if f.has_perm(user, 'embargo')]
        FOIARequest.objects.filter(pk__in=foias).update(embargo=False)
        return 'Embargoes removed'

    def _perm_embargo(self, foias, user, _post):
        """Permanently embargo the selected requests"""
        foias = [f.pk for f in foias if f.has_perm(user, 'embargo_perm')]
        FOIARequest.objects.filter(pk__in=foias).update(embargo=True)
        # only set permanent
        FOIARequest.objects.filter(
            pk__in=foias,
            status__in=END_STATUS,
        ).update(permanent_embargo=True)
        return 'Embargoes extended permanently'

    def _project(self, foias, user, post):
        """Add the requests to the selected projects"""
        foias = [f for f in foias if f.has_perm(user, 'change')]
        form = ProjectManagerForm(post, user=user)
        if form.is_valid():
            projects = form.cleaned_data['projects']
            for foia in foias:
                foia.projects.add(*projects)
            return 'Requests added to projects'

    def _tags(self, foias, user, post):
        """Add tags to the selected requests"""
        foias = [f for f in foias if f.has_perm(user, 'change')]
        tags = [
            Tag.objects.get_or_create(name=t)
            for t in parse_tags(post.get('tags', ''))
        ]
        tags = [t for t, _ in tags]
        for foia in foias:
            foia.tags.add(*tags)
        return 'Tags added to requests'

    def _share(self, foias, user, post):
        """Share the requests with the selected users"""
        foias = [f for f in foias if f.has_perm(user, 'change')]
        form = FOIAAccessForm(post)
        if form.is_valid():
            access = form.cleaned_data['access']
            users = form.cleaned_data['users']
            if access == 'edit':
                for foia in foias:
                    foia.read_collaborators.remove(*users)
                    foia.edit_collaborators.add(*users)
            elif access == 'view':
                for foia in foias:
                    foia.edit_collaborators.remove(*users)
                    foia.read_collaborators.add(*users)
            return 'Requests shared'

    def _autofollowup_on(self, foias, user, _post):
        """Turn autofollowups on"""
        return self._autofollowup(foias, user, disable=False)

    def _autofollowup_off(self, foias, user, _post):
        """Turn autofollowups off"""
        return self._autofollowup(foias, user, disable=True)

    def _autofollowup(self, foias, user, disable):
        """Set autofollowups"""
        foias = [f.pk for f in foias if f.has_perm(user, 'change')]
        FOIARequest.objects.filter(
            pk__in=foias,
        ).update(
            disable_autofollowups=disable,
        )
        action = 'disabled' if disable else 'enabled'
        return 'Autofollowups {}'.format(action)


@class_view_decorator(
    user_passes_test(lambda u: u.is_authenticated and u.profile.get_org())
)
class MyOrgRequestList(RequestList):
    """View requests owned by current user's organization"""
    filter_class = FOIARequestFilterSet
    title = 'Organization Requests'
    template_name = 'foia/list.html'

    def get_queryset(self):
        """Limit to just requests owned by the current user."""
        queryset = super(MyOrgRequestList, self).get_queryset()
        return queryset.filter(
            composer__user__profile__organization=self.request.user.profile.
            get_org()
        )


@class_view_decorator(
    user_passes_test(
        lambda u: u.is_authenticated and u.profile.acct_type == 'agency'
    )
)
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
class FollowingRequestList(RequestList):
    """List of all FOIA requests the user is following"""
    title = 'Requests You Follow'

    def get_queryset(self):
        """Limits FOIAs to those followed by the current user"""
        queryset = super(FollowingRequestList, self).get_queryset()
        followed = [
            f.pk
            for f in following(self.request.user, FOIARequest)
            if f is not None
        ]
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
        'date_submitted': 'composer__datetime_submitted',
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
        return objects.prefetch_related('communications').filter(
            status='submitted'
        )


@class_view_decorator(login_required)
class ComposerList(MRListView):
    """List to view your composers"""
    model = FOIAComposer
    title = 'Your Drafts'
    template_name = 'foia/composer_list.html'
    default_sort = 'datetime_created'
    default_order = 'desc'
    sort_map = {
        'title': 'title',
        'date_created': 'datetime_created',
    }

    def get_queryset(self):
        """Only show the current user's drafts"""
        return (
            super(ComposerList, self).get_queryset()
            .filter(user=self.request.user,
                    status='started').prefetch_related('agencies')
        )
