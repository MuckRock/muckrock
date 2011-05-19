"""
Views for the FOIA application
"""

from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string
from django.template import RequestContext
from django.views.generic import list_detail

from collections import namedtuple
from datetime import datetime

from foia.forms import FOIARequestForm, FOIADeleteForm, FOIAFixForm, FOIAFlagForm, \
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
                                  Q(jurisdiction=foia.jurisdiction, user=request.user) |
                                  Q(pk=agency_pk))
        return form

    if request.method == 'POST':
        status_dict = {'Submit Request': 'submitted', 'Save as Draft': 'started'}

        try:
            foia.status = status_dict[request.POST['submit']]

            form = default_form(request.POST)

            if form.is_valid():

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
                foia_comm.save()

                if request.POST['submit'] == 'Submit Request':
                    if request.user.get_profile().make_request():
                        foia.save()
                        foia.submit()
                        messages.success(request, 'Request succesfully submitted.')
                    else:
                        foia.status = 'started'
                        foia.save()
                        messages.error(request, "You are out of requests for this month.  "
                            "You're request has been saved as a draft, please submit it when you "
                            "get more requests")

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

    if action.must_own and foia.user != request.user:
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

Action = namedtuple('Action', 'form_actions msg tests form_class return_url heading value must_own')

def _save_foia_comm(request, foia, form):
    """Save the FOI Communication"""
    FOIACommunication.objects.create(
            foia=foia, from_who=request.user.get_full_name(), to_who=foia.get_to_who(),
            date=datetime.now(), response=False, full_html=False,
            communication=form.cleaned_data['comm'])
    foia.status = 'submitted'
    foia.save()
    foia.submit()

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
        value = 'Fix',
        must_own = True)
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
        value = 'Appeal',
        must_own = True)
    return _foia_action(request, jurisdiction, slug, idx, action)

@login_required
def flag(request, jurisdiction, slug, idx):
    """Flag a FOI Request as having incorrect information"""

    def form_actions(request, foia, form):
        """Email the admin about the flag"""

        send_mail('[FLAG] Freedom of Information Request: %s' % foia.title,
                  render_to_string('foia/flag.txt',
                                   {'request': foia, 'user': request.user,
                                    'reason': form.cleaned_data.get('reason')}),
                  'info@muckrock.com', ['requests@muckrock.com'], fail_silently=False)
        messages.info(request, 'Request succesfully flagged')

    action = Action(
        form_actions = form_actions,
        msg = 'flag',
        tests = [],
        form_class = lambda _: FOIAFlagForm,
        return_url = lambda r, f: f.get_absolute_url(),
        heading = 'Flag FOIA Request',
        value = 'Flag',
        must_own = False)
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
        value = 'Add',
        must_own = True)
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
        value = 'Delete',
        must_own = True)
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
        value = 'Update',
        must_own = True)
    return _foia_action(request, jurisdiction, slug, idx, action)

def _sort_requests(get, foia_requests):
    """Sort's the FOIA requests"""
    order = get.get('order', 'desc')
    field = get.get('field', 'date_submitted')

    if order not in ['asc', 'desc']:
        order = 'desc'
    if field not in ['title', 'status', 'user', 'jurisdiction', 'date']:
        field = 'date_submitted'

    if field == 'date':
        field = 'date_submitted'
    if field == 'jurisdiction':
        field += '__name'

    ob_field = '-' + field if order == 'desc' else field

    return foia_requests.order_by('-updated', ob_field)

def _list(request, requests, kwargs=None):
    """Helper function for creating list views"""
    # pylint: disable-msg=W0142

    if not kwargs:
        kwargs = {}

    per_page = min(int(request.GET.get('per_page', 10)), 100)
    return list_detail.object_list(request, requests, paginate_by=per_page,
                                   extra_context={'title': 'FOI Requests'}, **kwargs)

def list_(request):
    """List all viewable FOIA requests"""

    foia_requests = _sort_requests(request.GET, FOIARequest.objects.get_viewable(request.user))
    return _list(request, foia_requests)

def list_by_user(request, user_name):
    """List of all FOIA requests by a given user"""

    user = get_object_or_404(User, username=user_name)
    foia_requests = _sort_requests(request.GET,
                                   FOIARequest.objects.get_viewable(request.user).filter(user=user))

    return _list(request, foia_requests)

@login_required
def my_list(request, view):
    """Views owned by current user"""
    # pylint: disable-msg=E1103

    unsorted = FOIARequest.objects.filter(user=request.user)
    if view == 'drafts':
        unsorted = unsorted.get_editable()
    elif view == 'action':
        unsorted = unsorted.filter(status__in=['fix', 'payment'])
    elif view == 'waiting':
        unsorted = unsorted.filter(status='processed')
    elif view == 'completed':
        unsorted = unsorted.filter(status__in=['rejected', 'no_docs', 'done', 'partial'])

    foia_requests = _sort_requests(request.GET, unsorted)

    return _list(request, foia_requests, kwargs={'template_name': 'foia/foiarequest_mylist.html'})

def detail(request, jurisdiction, slug, idx):
    """Details of a single FOIA request"""

    jmodel = get_object_or_404(Jurisdiction, slug=jurisdiction)
    foia = get_object_or_404(FOIARequest, jurisdiction=jmodel, slug=slug, id=idx)

    if not foia.is_viewable(request.user):
        raise Http404()

    if foia.updated and foia.user == request.user:
        foia.updated = False
        foia.save()

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
