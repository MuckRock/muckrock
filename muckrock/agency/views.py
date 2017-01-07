"""
Views for the Agency application
"""

from django.contrib import messages
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext

from rest_framework import viewsets
import django_filters

from muckrock.agency.filters import AgencyFilterSet
from muckrock.agency.models import Agency
from muckrock.agency.serializers import AgencySerializer
from muckrock.jurisdiction.forms import FlagForm
from muckrock.jurisdiction.views import collect_stats
from muckrock.task.models import FlaggedTask
from muckrock.views import MRSearchFilterListView

class AgencyList(MRSearchFilterListView):
    """Filterable list of agencies"""
    model = Agency
    filter_class = AgencyFilterSet
    title = 'Agencies'
    template_name = 'agency/list.html'
    default_sort = 'name'

    def get_queryset(self):
        """Limit agencies to only approved ones."""
        approved = super(AgencyList, self).get_queryset().get_approved()
        approved = approved.select_related(
            'jurisdiction',
            'jurisdiction__parent',
            'jurisdiction__parent__parent',
        )
        return approved


def detail(request, jurisdiction, jidx, slug, idx):
    """Details for an agency"""

    agency = get_object_or_404(
            Agency.objects.select_related(
                'jurisdiction',
                'jurisdiction__parent',
                'jurisdiction__parent__parent'),
            jurisdiction__slug=jurisdiction,
            jurisdiction__pk=jidx,
            slug=slug,
            pk=idx,
            status='approved')

    foia_requests = agency.get_requests()
    foia_requests = (foia_requests.get_viewable(request.user)
        .get_submitted()
        .filter(agency=agency)
        .select_related(
          'jurisdiction',
          'jurisdiction__parent',
          'jurisdiction__parent__parent',
        )
        .order_by('-date_submitted')[:10])

    if request.method == 'POST':
        action = request.POST.get('action')
        form = FlagForm(request.POST)
        if action == 'flag':
            if form.is_valid():
                FlaggedTask.objects.create(
                    user=request.user,
                    text=form.cleaned_data.get('reason'),
                    agency=agency)
                messages.success(request, 'Correction submitted. Thanks!')
                return redirect(agency)
        elif action == 'mark_stale' and request.user.is_staff:
            task = agency.mark_stale(manual=True)
            messages.success(request, 'Agency marked as stale.')
            return redirect(reverse('stale-agency-task', kwargs={'pk': task.pk}))
    else:
        form = FlagForm()

    context = {
        'agency': agency,
        'foia_requests': foia_requests,
        'form': form,
        'sidebar_admin_url': reverse('admin:agency_agency_change', args=(agency.pk,)),
    }

    collect_stats(agency, context)

    return render_to_response('profile/agency.html', context,
                              context_instance=RequestContext(request))


def redirect_old(request, jurisdiction, slug, idx, action):
    """Redirect old urls to new urls"""
    # pylint: disable=unused-variable
    # pylint: disable=unused-argument

    # some jurisdiction slugs changed, just ignore the jurisdiction slug passed in
    agency = get_object_or_404(Agency, pk=idx)
    jurisdiction = agency.jurisdiction.slug
    jidx = agency.jurisdiction.pk

    if action == 'view':
        return redirect('/agency/%(jurisdiction)s-%(jidx)s/%(slug)s-%(idx)s/' % locals())

    return redirect('/agency/%(jurisdiction)s-%(jidx)s/%(slug)s-%(idx)s/%(action)s/' % locals())


def redirect_flag(request, jurisdiction, jidx, slug, idx):
    #pylint: disable=unused-argument
    """Redirect flag urls to base agency"""
    return redirect('agency-detail', jurisdiction, jidx, slug, idx)


class AgencyViewSet(viewsets.ModelViewSet):
    """API views for Agency"""
    # pylint: disable=too-many-ancestors
    # pylint: disable=too-many-public-methods
    queryset = (Agency.objects
            .select_related('jurisdiction', 'parent', 'appeal_agency')
            .prefetch_related('types')
            )
    serializer_class = AgencySerializer

    class Filter(django_filters.FilterSet):
        """API Filter for Agencies"""
        # pylint: disable=too-few-public-methods
        jurisdiction = django_filters.NumberFilter(name='jurisdiction__id')
        types = django_filters.CharFilter(name='types__name')
        class Meta:
            model = Agency
            fields = ('name', 'status', 'jurisdiction', 'types')

    filter_class = Filter
