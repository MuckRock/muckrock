"""
Views for the FOIA application
"""

from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template.defaultfilters import slugify
from django.template import RequestContext
from django.views.generic import list_detail

from collections import namedtuple
from datetime import datetime

from foia.forms import FOIARequestForm, FOIADeleteForm, FOIAFixForm, \
                       FOIANoteForm, FOIAEmbargoForm, FOIAEmbargoDateForm, FOIAAppealForm, \
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
                foia_comm = foia.communications.all()[0]
                foia_comm.date = datetime.now()
                foia_comm.communication = form.cleaned_data['request']
                if request.POST['submit'] == 'Submit Request':
                    foia_comm.communication += \
                        '\nFiled via MuckRock.com\n' \
                        'E-mail (Preferred): requests@muckrock.com\n' \
                        'Daytime: (617) 299-1832\n' \
                        'For mailed responses, please address:\n' \
                        'MuckRock\n' \
                        '185 Beacon St. #3\n' \
                        'Somerville, MA 02143'
                foia_comm.save()
                foia.save()

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
def update(request, jurisdiction, slug, idx):
    """Update a started FOIA Request"""

    jmodel = Jurisdiction.objects.get(slug=jurisdiction)
    foia = get_object_or_404(FOIARequest, jurisdiction=jmodel, slug=slug, id=idx)

    if not foia.is_editable():
        return render_to_response('error.html',
                 {'message': 'You may only edit non-submitted requests'},
                 context_instance=RequestContext(request))
    if foia.user != request.user:
        return render_to_response('error.html',
                 {'message': 'You may only edit your own requests'},
                 context_instance=RequestContext(request))

    return _foia_form_handler(request, foia, 'Update')

def _foia_action(request, jurisdiction, slug, idx, action):
    """Generic helper for FOIA actions"""

    jmodel = Jurisdiction.objects.get(slug=jurisdiction)
    foia = get_object_or_404(FOIARequest, jurisdiction=jmodel, slug=slug, pk=idx)
    form_class = action.form_class(foia)

    if foia.user != request.user:
        return render_to_response('error.html',
                 {'message': 'You may only %s your own requests' % action.msg},
                 context_instance=RequestContext(request))

    for test, msg in action.tests:
        if not test(foia):
            return render_to_response('error.html', {'message': msg},
                     context_instance=RequestContext(request))

    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            action.form_actions(request, foia, form)
            return HttpResponseRedirect(action.return_url(request, foia))

    else:
        if issubclass(form_class, forms.ModelForm):
            form = form_class(instance=foia)
        else:
            form = form_class()

    return render_to_response('foia/foiarequest_action.html',
                              {'form': form, 'foia': foia,
                               'heading': action.heading,
                               'action': action.value},
                              context_instance=RequestContext(request))

Action = namedtuple('Action', 'form_actions msg tests form_class return_url heading value')

def _save_foia_comm(request, foia, form):
    """Save the FOI Communication"""
    FOIACommunication.objects.create(
            foia=foia, from_who=request.user.get_full_name(), date=datetime.now(),
            response=False, full_html=False, communication=form.cleaned_data['comm'])
    foia.status = 'submitted'
    foia.save()

@login_required
def fix(request, jurisdiction, slug, idx):
    """Ammend a 'fix required' FOIA Request"""

    action = Action(
        form_actions = _save_foia_comm,
        msg = 'fix',
        tests = [(lambda f: f.is_fixable(), 'This request has not had a fix request')],
        form_class = lambda _: FOIAFixForm,
        return_url = lambda r, f: f.get_absolute_url(),
        heading = 'Fix FOIA Request',
        value = 'Fix')
    return _foia_action(request, jurisdiction, slug, idx, action)

@login_required
def appeal(request, jurisdiction, slug, idx):
    """Appeal a rejected FOIA Request"""

    action = Action(
        form_actions = _save_foia_comm,
        msg = 'appeal',
        tests = [(lambda f: f.is_appealable(), 'This request has not been rejected')],
        form_class = lambda _: FOIAAppealForm,
        return_url = lambda r, f: f.get_absolute_url(),
        heading = 'Appeal FOIA Request',
        value = 'Appeal')
    return _foia_action(request, jurisdiction, slug, idx, action)

@login_required
def note(request, jurisdiction, slug, idx):
    """Add a note to a request"""

    def form_actions(_, foia, form):
        """Save the FOI note"""
        foia_note = form.save(commit=False)
        foia_note.foia = foia
        foia_note.date = datetime.now()
        foia_note.save()

    action = Action(
        form_actions = form_actions,
        msg = 'add notes',
        tests = [],
        form_class = lambda _: FOIANoteForm,
        return_url = lambda r, f: f.get_absolute_url() + '#tabs-notes',
        heading = 'Add Note',
        value = 'Add')
    return _foia_action(request, jurisdiction, slug, idx, action)

@login_required
def delete(request, jurisdiction, slug, idx):
    """Delete a non-submitted FOIA Request"""

    def form_actions(request, foia, _):
        """Delete the FOI request"""
        foia.delete()
        messages.info(request, 'Request succesfully deleted')

    action = Action(
        form_actions = form_actions,
        msg = 'delete',
        tests = [(lambda f: f.is_deletable(), 'You may only delete draft requests.')],
        form_class = lambda _: FOIADeleteForm,
        return_url = lambda r, f: reverse('foia-list-user', kwargs={'user_name': r.user.username}),
        heading = 'Delete FOI Request',
        value = 'Delete')
    return _foia_action(request, jurisdiction, slug, idx, action)

@login_required
def embargo(request, jurisdiction, slug, idx):
    """Change the embargo on a request"""

    def form_actions(_, foia, form):
        """Update the embargo date"""
        foia.embargo = form.cleaned_data.get('embargo')
        foia.date_embargo = form.cleaned_data.get('date_embargo')
        foia.save()

    action = Action(
        form_actions = form_actions,
        msg = 'embargo',
        tests = [],
        form_class = lambda f: FOIAEmbargoDateForm if f.status in ['done', 'partial'] \
                               else FOIAEmbargoForm,
        return_url = lambda r, f: f.get_absolute_url(),
        heading = 'Update the Embargo Date',
        value = 'Update')
    return _foia_action(request, jurisdiction, slug, idx, action)

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

    context = {'object': foia, 'communications': foia.get_communications(request.user)}
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
