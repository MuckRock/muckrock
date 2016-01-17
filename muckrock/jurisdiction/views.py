"""
Views for the Jurisdiction application
"""

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models import Count, Sum
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext

from rest_framework import viewsets

from muckrock.foia.models import FOIARequest
from muckrock.jurisdiction.forms import FlagForm, JurisdictionFilterForm
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.jurisdiction.serializers import JurisdictionSerializer
from muckrock.task.models import FlaggedTask
from muckrock.views import MRFilterableListView

def collect_stats(obj, context):
    """Helper for collecting stats"""
    statuses = ('rejected', 'ack', 'processed', 'fix', 'no_docs', 'done', 'appealing')
    status_counts = (obj.foiarequest_set
        .filter(status__in=statuses)
        .order_by('status')
        .values_list('status')
        .annotate(Count('status')))
    context.update({'num_%s' % s: c for s, c in status_counts})
    context['num_overdue'] = obj.foiarequest_set.get_overdue().count()
    context['num_submitted'] = obj.foiarequest_set.get_submitted().count()


def detail(request, fed_slug, state_slug, local_slug):
    """Details for a jurisdiction"""

    jurisdiction = get_object_or_404(Jurisdiction, slug=fed_slug)
    if state_slug:
        jurisdiction = get_object_or_404(Jurisdiction, slug=state_slug, parent=jurisdiction)
    if local_slug:
        jurisdiction = get_object_or_404(Jurisdiction, slug=local_slug, parent=jurisdiction)

    foia_requests = (FOIARequest.objects.get_viewable(request.user)
                                       .filter(jurisdiction=jurisdiction)
                                       .order_by('-date_submitted')
                                       .select_related_view()[:5])

    agencies = (jurisdiction.agencies.get_approved()
            .only('pk', 'slug', 'name', 'jurisdiction')
            .annotate(foia_count=Count('foiarequest'))
            .annotate(pages=Sum('foiarequest__files__pages'))
            .order_by('name')
            [:15])

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
            messages.info(request, 'Correction submitted, thanks.')
            return redirect(jurisdiction)
    else:
        form = FlagForm()

    context = {
        'jurisdiction': jurisdiction,
        'agencies': agencies,
        'foia_requests': foia_requests,
        'form': form,
        'sidebar_admin_url': reverse('admin:jurisdiction_jurisdiction_change',
            args=(jurisdiction.pk,)),
    }

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
        objects = objects.exclude(hidden=True)
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

# pylint: disable=unused-argument
def redirect_flag(request, **kwargs):
    """Redirect flag urls to base agency"""
    # filter None from kwargs
    kwargs = dict((key, kwargs[key]) for key in kwargs if kwargs[key] is not None)
    return redirect('jurisdiction-detail', **kwargs)

class JurisdictionViewSet(viewsets.ModelViewSet):
    """API views for Jurisdiction"""
    # pylint: disable=too-many-ancestors
    # pylint: disable=too-many-public-methods
    queryset = Jurisdiction.objects.all()
    serializer_class = JurisdictionSerializer
    filter_fields = ('name', 'abbrev', 'level', 'parent')
