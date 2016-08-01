"""
Views for the Jurisdiction application
"""

from django.contrib import messages
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models import Count, Sum, Q
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.views.generic import DetailView

from rest_framework import viewsets

from muckrock.agency.models import Agency
from muckrock.jurisdiction.forms import FlagForm, JurisdictionFilterForm
from muckrock.jurisdiction.models import Jurisdiction, Exemption
from muckrock.jurisdiction.serializers import JurisdictionSerializer
from muckrock.task.models import FlaggedTask
from muckrock.views import MRFilterableListView


def collect_stats(obj, context):
    """Helper for collecting stats"""
    statuses = ('rejected', 'ack', 'processed', 'fix', 'no_docs', 'done', 'appealing')
    requests = obj.get_requests()
    status_counts = (requests
        .filter(status__in=statuses)
        .order_by('status')
        .values_list('status')
        .annotate(Count('status')))
    context.update({'num_%s' % s: c for s, c in status_counts})
    context['num_overdue'] = requests.get_overdue().count()
    context['num_submitted'] = requests.get_submitted().count()


def detail(request, fed_slug, state_slug, local_slug):
    """Details for a jurisdiction"""
    if local_slug:
        jurisdiction = get_object_or_404(
                Jurisdiction.objects.select_related(
                    'parent',
                    'parent__parent',
                    ),
                slug=local_slug,
                parent__slug=state_slug,
                parent__parent__slug=fed_slug)
    elif state_slug:
        jurisdiction = get_object_or_404(
                Jurisdiction.objects.select_related('parent'),
                slug=state_slug,
                parent__slug=fed_slug)
    else:
        jurisdiction = get_object_or_404(Jurisdiction,
                slug=fed_slug)

    foia_requests = jurisdiction.get_requests()
    foia_requests = (foia_requests.get_viewable(request.user)
                                  .get_done()
                                  .order_by('-date_done')
                                  .select_related_view()
                                  .get_public_file_count(limit=10)[:10])

    if jurisdiction.level == 's':
        agencies = Agency.objects.filter(
            Q(jurisdiction=jurisdiction)|
            Q(jurisdiction__parent=jurisdiction)
        )
    else:
        agencies = jurisdiction.agencies
    agencies = (agencies.get_approved()
                        .only('pk', 'slug', 'name', 'jurisdiction')
                        .annotate(foia_count=Count('foiarequest'))
                        .annotate(pages=Sum('foiarequest__files__pages'))
                        .order_by('-foia_count')[:10])

    _children = Jurisdiction.objects.filter(parent=jurisdiction).select_related('parent__parent')
    _top_children = (_children.annotate(foia_count=Count('foiarequest'))
                              .annotate(pages=Sum('foiarequest__files__pages'))
                              .order_by('-foia_count')[:10])

    if request.method == 'POST':
        form = FlagForm(request.POST)
        if form.is_valid():
            user = None
            if request.user.is_authenticated():
                user = request.user
            FlaggedTask.objects.create(
                user=user,
                text=form.cleaned_data.get('reason'),
                jurisdiction=jurisdiction)
            messages.success(request, 'We received your feedback. Thanks!')
            return redirect(jurisdiction)
    else:
        form = FlagForm()

    admin_url = reverse('admin:jurisdiction_jurisdiction_change', args=(jurisdiction.pk,))
    context = {
        'jurisdiction': jurisdiction,
        'agencies': agencies,
        'children': _children,
        'top_children': _top_children,
        'foia_requests': foia_requests,
        'form': form,
        'sidebar_admin_url': admin_url,
        'title': jurisdiction.name + ' Public Records Guide'
    }
    if request.user.is_staff and jurisdiction.abbrev:
        context['proxies'] = User.objects.filter(
            profile__acct_type='proxy',
            profile__state=jurisdiction.abbrev,
            )
    collect_stats(jurisdiction, context)

    return render_to_response('profile/jurisdiction.html', context,
                              context_instance=RequestContext(request))


class List(MRFilterableListView):
    """Filterable list of jurisdictions"""
    model = Jurisdiction
    title = 'Jurisdictions'
    template_name = 'lists/jurisdiction_list.html'
    default_sort = 'name'

    def get_queryset(self):
        """Hides hidden jurisdictions from list"""
        objects = super(List, self).get_queryset()
        objects = (objects
                .exclude(hidden=True)
                .select_related('parent', 'parent__parent'))
        return objects

    def get_filters(self):
        base_filters = super(List, self).get_filters()
        new_filters = [
            {'field': 'level', 'lookup': 'exact'},
            {'field': 'parent', 'lookup': 'exact'},
        ]
        return base_filters + new_filters

    def get_context_data(self, **kwargs):
        context = super(List, self).get_context_data(**kwargs)
        filter_data = self.get_filter_data()
        context['filter_form'] = JurisdictionFilterForm(initial=filter_data['filter_initials'])
        return context


def redirect_flag(request, **kwargs):
    """Redirect flag urls to base agency"""
    # pylint: disable=unused-argument
    # filter None from kwargs
    kwargs = dict((key, kwargs[key]) for key in kwargs if kwargs[key] is not None)
    return redirect('jurisdiction-detail', **kwargs)


class JurisdictionViewSet(viewsets.ModelViewSet):
    """API views for Jurisdiction"""
    # pylint: disable=too-many-ancestors
    # pylint: disable=too-many-public-methods
    queryset = Jurisdiction.objects.select_related('parent__parent').order_by()
    serializer_class = JurisdictionSerializer
    filter_fields = ('name', 'abbrev', 'level', 'parent')


class ExemptionDetailView(DetailView):
    """Detail view for an individual exemption"""
    model = Exemption
    template_name = 'exemption/detail.html'
