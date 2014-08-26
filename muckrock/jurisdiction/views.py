"""
Views for the Jurisdiction application
"""

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.template.loader import render_to_string

from rest_framework import viewsets

from muckrock.foia.models import FOIARequest
from muckrock.jurisdiction.forms import FlagForm
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.jurisdiction.serializers import JurisdictionSerializer
from muckrock.sidebar.models import Sidebar

def collect_stats(obj, context):
    """Helper for collecting stats"""
    for status in ['rejected', 'ack', 'processed', 'fix', 'no_docs', 'done', 'appealing']:
        context['num_%s' % status] = obj.foiarequest_set.filter(status=status).count()
    context['num_overdue'] = obj.foiarequest_set.get_overdue().count()
    context['num_submitted'] = obj.foiarequest_set.get_submitted().count()
    context['submitted_reqs'] = obj.foiarequest_set.get_public().order_by('-date_submitted')[:5]
    context['overdue_reqs'] = obj.foiarequest_set.get_public() \
                                 .get_overdue().order_by('date_due')[:5]

# TODO: Move the `flag` view into the `detail` view
def flag_helper(request, obj, type_):
    """Helper for flagging jurisdictions and agencies"""

    if request.method == 'POST':
        form = FlagForm(request.POST)
        if form.is_valid():
            send_mail('[FLAG] %s: %s' % (type_, obj.name),
                      render_to_string('jurisdiction/flag.txt',
                                       {'obj': obj, 'user': request.user, 'type': type_,
                                        'reason': form.cleaned_data.get('reason')}),
                      'info@muckrock.com', ['requests@muckrock.com'], fail_silently=False)
            messages.info(request, 'Agency correction succesfully submitted')
            return redirect(obj)
    else:
        form = FlagForm()
    return render_to_response('jurisdiction/flag.html',
                              {'form': form, 'obj': obj, 'type': type_,
                               'base': '%s/base.html' % type_},
                              context_instance=RequestContext(request))

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

    context = {'jurisdiction': jurisdiction, 'foia_requests': foia_requests}
    if request.user.is_anonymous():
        context['sidebar'] = Sidebar.objects.get_text('anon_jurisdiction')
    else:
        context['sidebar'] = Sidebar.objects.get_text('jurisdiction')
    collect_stats(jurisdiction, context)

    return render_to_response('details/jurisdiction_detail.html', context,
                              context_instance=RequestContext(request))

def list_(request):
    """List of jurisdictions"""
    fed_jurs = Jurisdiction.objects.filter(level='f')
    state_jurs = Jurisdiction.objects.filter(level='s')
    context = {'fed_jurs': fed_jurs, 'state_jurs': state_jurs}

    return render_to_response('lists/jurisdiction_list.html', context,
                              context_instance=RequestContext(request))

@login_required
def flag(request, fed_slug, state_slug, local_slug):
    """Flag a correction for a jurisdiction's information"""

    jurisdiction = get_object_or_404(Jurisdiction, slug=fed_slug)
    if state_slug:
        jurisdiction = get_object_or_404(Jurisdiction, slug=state_slug, parent=jurisdiction)
    if local_slug:
        jurisdiction = get_object_or_404(Jurisdiction, slug=local_slug, parent=jurisdiction)

    return flag_helper(request, jurisdiction, 'jurisdiction')


class JurisdictionViewSet(viewsets.ModelViewSet):
    """API views for Jurisdiction"""
    # pylint: disable=R0901
    # pylint: disable=R0904
    queryset = Jurisdiction.objects.all()
    serializer_class = JurisdictionSerializer
    filter_fields = ('name', 'abbrev', 'level', 'parent')
