"""
Views for the Jurisdiction application
"""

from django.contrib import messages
from django.core.urlresolvers import reverse
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
    for status in ['rejected', 'ack', 'processed', 'fix', 'no_docs', 'done', 'appealing']:
        context['num_%s' % status] = obj.foiarequest_set.filter(status=status).count()
    context['num_overdue'] = obj.foiarequest_set.get_overdue().count()
    context['num_submitted'] = obj.foiarequest_set.get_submitted().count()
    context['submitted_reqs'] = obj.foiarequest_set.get_public().order_by('-date_submitted')[:5]
    context['overdue_reqs'] = obj.foiarequest_set.get_public() \
                                 .get_overdue().order_by('date_due')[:5]


def detail(request, fed_slug, state_slug, local_slug):
    """Details for a jurisdiction"""

    jurisdiction = get_object_or_404(Jurisdiction, slug=fed_slug)
    if state_slug:
        jurisdiction = get_object_or_404(Jurisdiction, slug=state_slug, parent=jurisdiction)
    if local_slug:
        jurisdiction = get_object_or_404(Jurisdiction, slug=local_slug, parent=jurisdiction)

    foia_requests = FOIARequest.objects.get_viewable(request.user)\
                                       .filter(jurisdiction=jurisdiction)\
                                       .order_by('-date_submitted')[:5]

    if request.method == 'POST':
        form = FlagForm(request.POST)
        if form.is_valid():
            FlaggedTask.objects.create(
                user=request.user,
                text=form.cleaned_data.get('reason'),
                jurisdiction=jurisdiction)
            messages.info(request, 'Correction submitted, thanks.')
            return redirect(jurisdiction)
    else:
        form = FlagForm()

    context = {
        'jurisdiction': jurisdiction,
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
