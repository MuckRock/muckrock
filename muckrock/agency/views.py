"""
Views for the Agency application
"""

from django.contrib import messages
from django.core.mail import send_mail
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.http import Http404
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.template.loader import render_to_string

from rest_framework import viewsets
import django_filters

from muckrock.agency.models import Agency
from muckrock.agency.serializers import AgencySerializer
from muckrock.foia.models import FOIARequest
from muckrock.jurisdiction.forms import FlagForm
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.jurisdiction.views import collect_stats

def detail(request, jurisdiction, jidx, slug, idx):
    """Details for an agency"""

    jmodel = get_object_or_404(Jurisdiction, slug=jurisdiction, pk=jidx)
    agency = get_object_or_404(Agency, jurisdiction=jmodel, slug=slug, pk=idx)

    if not agency.approved:
        raise Http404()

    foia_requests = FOIARequest.objects.get_viewable(request.user)\
                                       .filter(agency=agency)\
                                       .order_by('-date_submitted')[:5]

    if request.method == 'POST':
        form = FlagForm(request.POST)
        if form.is_valid():
            send_mail(
                '[FLAG] Agency: %s' % agency.name,
                render_to_string(
                    'text/jurisdiction/flag.txt', {
                        'obj': agency,
                        'user': request.user,
                        'type': 'agency',
                        'reason': form.cleaned_data.get('reason')
                    }
                ),
                'info@muckrock.com',
                ['requests@muckrock.com'],
                fail_silently=False
            )
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

    return render_to_response('details/agency_detail.html', context,
                              context_instance=RequestContext(request))

def list_(request):
    """List of popular agencies"""
    agencies = Agency.objects.annotate(num_requests=Count('foiarequest')) \
                             .order_by('-num_requests')[:10]
    context = {'object_list': agencies}

    return render_to_response('lists/agency_list.html', context,
                              context_instance=RequestContext(request))

def redirect_old(request, jurisdiction, slug, idx, action):
    """Redirect old urls to new urls"""
    # pylint: disable=W0612
    # pylint: disable=W0613

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
    # pylint: disable=R0901
    # pylint: disable=R0904
    queryset = Agency.objects.all()
    serializer_class = AgencySerializer

    class Filter(django_filters.FilterSet):
        """API Filter for Agencies"""
        # pylint: disable=E1101
        # pylint: disable=R0903
        jurisdiction = django_filters.CharFilter(name='jurisdiction__name')
        types = django_filters.CharFilter(name='types__name')
        class Meta:
            model = Agency
            fields = ('name', 'jurisdiction', 'types')

    filter_class = Filter
