"""
Views for the Agency application
"""

# Django
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.html import linebreaks

# Standard Library
import re

# Third Party
import django_filters
from fuzzywuzzy import fuzz, process
from rest_framework import viewsets

# MuckRock
from muckrock.agency.filters import AgencyFilterSet
from muckrock.agency.models import Agency
from muckrock.agency.serializers import AgencySerializer
from muckrock.agency.utils import initial_communication_template
from muckrock.jurisdiction.forms import FlagForm
from muckrock.jurisdiction.models import Jurisdiction
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
    sort_map = {
        'name': 'name',
        'jurisdiction': 'jurisdiction__slug',
    }

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
            'jurisdiction', 'jurisdiction__parent',
            'jurisdiction__parent__parent'
        ),
        jurisdiction__slug=jurisdiction,
        jurisdiction__pk=jidx,
        slug=slug,
        pk=idx,
        status='approved'
    )

    foia_requests = agency.get_requests()
    foia_requests = (
        foia_requests.get_viewable(request.user)
        .filter(agency=agency).select_related(
            'agency__jurisdiction__parent__parent',
        ).order_by('-composer__datetime_submitted')[:10]
    )

    if request.method == 'POST':
        action = request.POST.get('action')
        form = FlagForm(request.POST)
        if action == 'flag':
            if form.is_valid() and request.user.is_authenticated():
                FlaggedTask.objects.create(
                    user=request.user,
                    text=form.cleaned_data.get('reason'),
                    agency=agency
                )
                messages.success(request, 'Correction submitted. Thanks!')
                return redirect(agency)
        elif action == 'mark_stale' and request.user.is_staff:
            task = agency.mark_stale(manual=True)
            messages.success(request, 'Agency marked as stale.')
            return redirect(
                reverse('stale-agency-task', kwargs={
                    'pk': task.pk
                })
            )
    else:
        form = FlagForm()

    context = {
        'agency':
            agency,
        'foia_requests':
            foia_requests,
        'form':
            form,
        'sidebar_admin_url':
            reverse('admin:agency_agency_change', args=(agency.pk,)),
    }

    collect_stats(agency, context)

    return render(
        request,
        'profile/agency.html',
        context,
    )


def redirect_old(request, jurisdiction, slug, idx, action):
    """Redirect old urls to new urls"""
    # pylint: disable=unused-variable
    # pylint: disable=unused-argument

    # some jurisdiction slugs changed, just ignore the jurisdiction slug passed in
    agency = get_object_or_404(Agency, pk=idx)
    jurisdiction = agency.jurisdiction.slug
    jidx = agency.jurisdiction.pk

    if action == 'view':
        return redirect(
            '/agency/%(jurisdiction)s-%(jidx)s/%(slug)s-%(idx)s/' % locals()
        )

    return redirect(
        '/agency/%(jurisdiction)s-%(jidx)s/%(slug)s-%(idx)s/%(action)s/' %
        locals()
    )


def redirect_flag(request, jurisdiction, jidx, slug, idx):
    #pylint: disable=unused-argument
    """Redirect flag urls to base agency"""
    return redirect('agency-detail', jurisdiction, jidx, slug, idx)


class AgencyViewSet(viewsets.ModelViewSet):
    """API views for Agency"""
    # pylint: disable=too-many-public-methods
    queryset = (
        Agency.objects.order_by('id').select_related(
            'jurisdiction', 'parent', 'appeal_agency'
        ).prefetch_related('types')
    )
    serializer_class = AgencySerializer
    # don't allow ordering by computed fields
    ordering_fields = [
        f for f in AgencySerializer.Meta.fields if f not in (
            'absolute_url',
            'average_response_time',
            'fee_rate',
            'success_rate',
        )
    ]

    class Filter(django_filters.FilterSet):
        """API Filter for Agencies"""
        jurisdiction = django_filters.NumberFilter(name='jurisdiction__id')
        types = django_filters.CharFilter(name='types__name')

        class Meta:
            model = Agency
            fields = (
                'name', 'status', 'jurisdiction', 'types', 'requires_proxy'
            )

    filter_class = Filter


def similar(request):
    """Return agencies with similar names"""
    # TODO this is currently unused
    query = request.GET.get('query', '')
    jurisdiction_id = request.GET.get('jurisdiction')
    if jurisdiction_id == 'f':
        jurisdiction = Jurisdiction.objects.filter(level='f').first()
    elif not jurisdiction_id:
        jurisdiction = None
    else:
        jurisdiction = Jurisdiction.objects.filter(pk=jurisdiction_id).first()

    agencies = Agency.objects.filter(status='approved')
    if jurisdiction:
        agencies = agencies.filter(jurisdiction=jurisdiction)

    # if there is an exact match, do not bother fuzzy matching
    exact = agencies.filter(name__iexact=query).first()
    if exact:
        return JsonResponse({'exact': {'value': exact.pk, 'text': exact.name}})

    suggestions = process.extractBests(
        query,
        {a.pk: a.name
         for a in agencies},
        scorer=fuzz.token_set_ratio,
        score_cutoff=80,
        limit=10,
    )
    suggestions = [{'value': s[2], 'text': s[0]} for s in suggestions]
    return JsonResponse({'suggestions': suggestions})


def boilerplate(request):
    """Return the boilerplate language for requests to the given agency"""

    p_new = re.compile(r'\$new\$[^$]+\$[0-9]+\$')
    p_int = re.compile(r'[0-9]+')
    agency_pks = request.GET.getlist('agencies')
    new_agency_pks = [a for a in agency_pks if p_new.match(a)]
    other_agency_pks = [a for a in agency_pks if p_int.match(a)]

    agencies = Agency.objects.filter(pk__in=other_agency_pks)
    extra_jurisdictions = Jurisdiction.objects.filter(
        pk__in=[i.split('$')[3] for i in new_agency_pks]
    )
    if request.user.is_authenticated:
        user_name = request.user.get_full_name()
    else:
        user_name = (
            '<abbr title="This will be replaced by your full name">'
            '{ name }</abbr>'
        )
    split_token = '$split$'
    text = initial_communication_template(
        agencies,
        user_name,
        split_token,
        extra_jurisdictions=extra_jurisdictions,
        edited_boilerplate=False,
        proxy=False,
        html=True,
    )
    intro, outro = text.split(split_token)
    return JsonResponse({
        'intro': linebreaks(intro.strip()),
        'outro': linebreaks(outro.strip()),
    })


def contact_info(request, idx):
    """Return the agencies contact info"""
    agency = get_object_or_404(Agency, pk=idx)
    if request.user.is_anonymous or not request.user.profile.is_advanced():
        if agency.portal:
            type_ = 'portal'
        elif agency.email:
            type_ = 'email'
        elif agency.fax:
            type_ = 'fax'
        elif agency.address:
            type_ = 'snail'
        else:
            type_ = 'none'
        return JsonResponse({'type': type_})
    else:
        return JsonResponse({
            'portal': {
                'type': agency.portal.get_type_display(),
                'url': agency.url
            } if agency.portal else None,
            'emails': [{
                'value': e.pk,
                'display': unicode(e)
            } for e in agency.emails.filter(status='good')
                       .exclude(email__endswith='muckrock.com')],
            'faxes': [{
                'value': f.pk,
                'display': unicode(f)
            } for f in agency.phones.filter(status='good', type='fax')],
            'email':
                unicode(agency.email)
                if agency.email and agency.email.status == 'good' else None,
            'cc_emails': [unicode(e) for e in agency.other_emails],
            'fax':
                unicode(agency.fax)
                if agency.fax and agency.fax.status == 'good' else None,
            'address':
                unicode(agency.address) if agency.address else None,
        })
