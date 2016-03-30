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

from muckrock.agency.models import Agency
from muckrock.agency.serializers import AgencySerializer
from muckrock.foia.models import FOIARequest
from muckrock.jurisdiction.forms import FlagForm
from muckrock.jurisdiction.views import collect_stats
from muckrock.task.models import FlaggedTask
from muckrock.views import MRFilterableListView

class List(MRFilterableListView):
    """Filterable list of agencies"""
    model = Agency
    title = 'Agencies'
    template_name = 'lists/agency_list.html'
    default_sort = 'name'

    def get_queryset(self):
        """Limit agencies to only approved ones."""
        objects = (super(List, self)
                .get_queryset()
                .get_approved()
                .select_related(
                    'jurisdiction',
                    'jurisdiction__parent',
                    'jurisdiction__parent__parent',
                    ))
        return objects

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

    foia_requests = (FOIARequest.objects
            .get_viewable(request.user)
            .filter(agency=agency)
            .select_related(
                'jurisdiction',
                'jurisdiction__parent',
                'jurisdiction__parent__parent',
                )
            .order_by('-date_submitted')[:5])

    if request.method == 'POST':
        form = FlagForm(request.POST)
        if form.is_valid():
            FlaggedTask.objects.create(
                user=request.user,
                text=form.cleaned_data.get('reason'),
                agency=agency)
            messages.info(request, 'Correction submitted. Thanks!')
            return redirect(agency)
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

def stale(request):
    """List all stale agencies"""

    agencies = Agency.objects.filter(stale=True)
    paginator = Paginator(agencies, 15)
    try:
        page = paginator.page(request.GET.get('page'))
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)
    return render_to_response('lists/agency_stale_list.html',
                              {'object_list': page},
                              context_instance=RequestContext(request))


class AgencyViewSet(viewsets.ModelViewSet):
    """API views for Agency"""
    # pylint: disable=too-many-ancestors
    # pylint: disable=too-many-public-methods
    queryset = Agency.objects.all().select_related('jurisdiction', 'parent', 'appeal_agency')
    serializer_class = AgencySerializer

    class Filter(django_filters.FilterSet):
        """API Filter for Agencies"""
        # pylint: disable=too-few-public-methods
        jurisdiction = django_filters.NumberFilter(name='jurisdiction__id')
        types = django_filters.CharFilter(name='types__name')
        class Meta:
            model = Agency
            fields = ('name', 'jurisdiction', 'types')

    filter_class = Filter
