"""
Views for the FOIA application
"""

from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.forms.models import inlineformset_factory
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template.defaultfilters import slugify
from django.template import RequestContext
from django.views.generic import list_detail

from datetime import datetime

from foia.forms import FOIARequestForm, FOIARequestTrackerForm, FOIADeleteForm, \
                       FOIAWizardWhereForm, FOIAWhatLocalForm, FOIAWhatStateForm, \
                       FOIAWhatFederalForm, FOIAWizard, TEMPLATES
from foia.models import FOIARequest, FOIADocument, FOIACommunication, Jurisdiction, Agency

def _foia_form_handler(request, foia, action):
    """Handle a form for a FOIA request - user to update a FOIA request"""

    def default_form(data=None):
        """Make a default form to update a FOIA request"""
        if data:
            form = FOIARequestForm(data, instance=foia)
        else:
            form = FOIARequestForm(initial={'request': foia.first_request()}, instance=foia)
        agency_pk = foia.agency and foia.agency.pk
        form.fields['agency'].queryset = \
            Agency.objects.filter(Q(jurisdiction=foia.jurisdiction, approved=True) |
                                  Q(pk=agency_pk))
        return form

    if request.method == 'POST':
        status_dict = {'Submit Request': 'submitted', 'Save as Draft': 'started'}

        try:
            foia.status = status_dict[request.POST['submit']]

            form = default_form(request.POST)

            if form.is_valid():
                if request.POST['submit'] == 'Submit Request':
                    if not request.user.get_profile().make_request():
                        foia.status = 'started'
                        messages.error(request, "You are out of requests for this month.  "
                            "You're request has been saved as a draft, please submit it when you "
                            "get more requests")

                foia = form.save(commit=False)
                agency_name = request.POST.get('agency-name')
                if agency_name and (not foia.agency or agency_name != foia.agency.name):
                    # Use the combobox to create a new agency
                    foia.agency = Agency.objects.create(name=agency_name,
                                                        jurisdiction=foia.jurisdiction,
                                                        user=request.user, approved=False)
                foia.slug = slugify(foia.title)
                foia.save()
                foia_comm = foia.communications.all()[0]
                foia_comm.date = datetime.now()
                foia_comm.communication = form.cleaned_data['request']
                foia_comm.save()

                return HttpResponseRedirect(foia.get_absolute_url())

        except KeyError:
            # bad post, not possible from web form
            form = default_form()
    else:
        form = default_form()

    return render_to_response('foia/foiarequest_form.html',
                              {'form': form, 'action': action},
                              context_instance=RequestContext(request))

@login_required
def create(request):
    """Create a new foia request using the wizard"""

    # collect all the forms so that the wizard can access them
    form_dict = dict((t.__name__, t) for t in TEMPLATES.values())
    form_dict.update((form.__name__, form) for form in
                     [FOIAWizardWhereForm, FOIAWhatLocalForm,
                      FOIAWhatStateForm, FOIAWhatFederalForm])
    return FOIAWizard(['FOIAWizardWhereForm'], form_dict)(request)

@login_required
def tracker(request, foia=None):
    """Create or update a foia request just for tracking"""

    def default_form(data=None):
        """Make a default form for a tracker FOI request"""

        # pylint: disable-msg=C0103
        CommInlineFormset = inlineformset_factory(FOIARequest, FOIACommunication,
                extra=1, can_delete=False, fields=('from_who', 'date', 'communication'))
        if data:
            form = FOIARequestTrackerForm(data, instance=foia)
            formset = CommInlineFormset(data, instance=foia)
        else:
            form = FOIARequestTrackerForm(instance=foia)
            formset = CommInlineFormset(instance=foia)

        agency_pk = foia and foia.agency and foia.agency.pk
        form.fields['agency'].queryset = Agency.objects.filter(Q(approved=True) | Q(pk=agency_pk))
        for formset_form in formset.forms:
            formset_form.fields['date'].widget = forms.TextInput(attrs={'class': 'datepicker'})

        return form, formset

    if request.method == 'POST':
        form, formset = default_form(request.POST)
        if form.is_valid() and formset.is_valid():
            foia = form.save(commit=False)

            agency_name = request.POST.get('agency-name')
            if agency_name and (not foia.agency or agency_name != foia.agency.name):
                # Use the combobox to create a new agency
                foia.agency = Agency.objects.create(name=agency_name,
                                                    jurisdiction=foia.jurisdiction,
                                                    approved=False)
            foia.user = request.user
            foia.slug = slugify(foia.title)
            foia.tracker = True
            foia.save()
            comms = formset.save(commit=False)
            for comm in comms:
                comm.foia = foia
                comm.save()
            return HttpResponseRedirect(foia.get_absolute_url())
    else:
        form, formset = default_form()

    return render_to_response('foia/foiarequest_tracker_form.html',
                              {'form': form, 'formset': formset},
                              context_instance=RequestContext(request))

@login_required
def update(request, jurisdiction, slug, idx):
    """Update a started FOIA Request"""

    jmodel = Jurisdiction.objects.get(slug=jurisdiction)
    foia = get_object_or_404(FOIARequest, jurisdiction=jmodel, slug=slug, id=idx)

    if not foia.is_editable():
        return render_to_response('error.html',
                 {'message': 'You may only edit non-submitted requests unless a fix is requested'},
                 context_instance=RequestContext(request))
    if foia.user != request.user:
        return render_to_response('error.html',
                 {'message': 'You may only edit your own requests'},
                 context_instance=RequestContext(request))

    if foia.tracker:
        return tracker(request, foia)

    return _foia_form_handler(request, foia, 'Update')

@login_required
def delete(request, jurisdiction, slug, idx):
    """Delete a non-submitted FOIA Request"""

    jmodel = Jurisdiction.objects.get(slug=jurisdiction)
    foia = get_object_or_404(FOIARequest, jurisdiction=jmodel, slug=slug, id=idx)

    if not foia.is_deletable():
        return render_to_response('error.html',
                 {'message': 'You may only delete non-submitted requests.'},
                 context_instance=RequestContext(request))
    if foia.user != request.user:
        return render_to_response('error.html',
                 {'message': 'You may only delete your own requests'},
                 context_instance=RequestContext(request))

    if request.method == 'POST':
        form = FOIADeleteForm(request.POST)
        if form.is_valid():
            foia.delete()
            messages.info(request, 'Request succesfully deleted')
            return HttpResponseRedirect(reverse('foia-list-user',
                                                kwargs={'user_name': request.user.username}))
    else:
        form = FOIADeleteForm()

    return render_to_response('foia/foiarequest_delete.html',
                              {'form': form, 'foia': foia},
                              context_instance=RequestContext(request))

def _sort_requests(get, foia_requests):
    """Sort's the FOIA requests"""
    order = get.get('order', 'desc')
    field = get.get('field', 'date_submitted')
    if order not in ['asc', 'desc']:
        order = 'desc'
    if field not in ['title', 'status', 'user', 'jurisdiction', 'date_submitted']:
        field = 'date_submitted'
    if field == 'jurisdiction':
        field += '__name'
    ob_field = '-' + field if order == 'desc' else field

    return foia_requests.order_by(ob_field)

@login_required
def update_list(request):
    """List of all editable FOIA requests by a given user"""

    foia_requests = _sort_requests(request.GET,
                                   FOIARequest.objects.get_editable().filter(user=request.user))

    return list_detail.object_list(request, foia_requests, paginate_by=10,
                                   extra_context={'title': 'My Editable FOI Requests',
                                                  'base': 'foia/base-submit-single.html'})

def list_(request):
    """List all viewable FOIA requests"""

    foia_requests = _sort_requests(request.GET, FOIARequest.objects.get_viewable(request.user))

    return list_detail.object_list(
                request, foia_requests, paginate_by=10,
                extra_context={'title': 'FOI Requests', 'base': 'foia/base-single.html'})

def list_by_user(request, user_name):
    """List of all FOIA requests by a given user"""

    user = get_object_or_404(User, username=user_name)
    foia_requests = _sort_requests(request.GET,
                                   FOIARequest.objects.get_viewable(request.user).filter(user=user))

    return list_detail.object_list(request, foia_requests, paginate_by=10,
                                   extra_context={'title': 'FOI Requests',
                                                  'base': 'foia/base-single.html'})

def detail(request, jurisdiction, slug, idx):
    """Details of a single FOIA request"""

    jmodel = Jurisdiction.objects.get(slug=jurisdiction)
    foia = get_object_or_404(FOIARequest, jurisdiction=jmodel, slug=slug, id=idx)

    if not foia.is_viewable(request.user):
        raise Http404()

    context = {'object': foia}
    if foia.date_due:
        context['past_due'] = foia.date_due < datetime.now().date()
    else:
        context['past_due'] = False

    return render_to_response('foia/foiarequest_detail.html',
                              context,
                              context_instance=RequestContext(request))

def doc_cloud_detail(request, doc_id):
    """Details of a DocumentCloud document"""

    doc = get_object_or_404(FOIADocument, doc_id=doc_id)

    if not doc.is_viewable(request.user) or not doc.doc_id:
        raise Http404()

    return redirect(doc, permanant=True)
