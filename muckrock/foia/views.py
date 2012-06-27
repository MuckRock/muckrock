"""
Views for the FOIA application
"""

from django import forms
from django.contrib.auth.decorators import login_required, user_passes_test
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
from decimal import Decimal
import logging
import stripe
import sys

from agency.models import Agency
from accounts.forms import PaymentForm
from foia.forms import FOIARequestForm, FOIADeleteForm, FOIAAdminFixForm, FOIAFixForm, \
                       FOIAFlagForm, FOIANoteForm, FOIAEmbargoForm, FOIAEmbargoDateForm, \
                       FOIAAppealForm, FOIAWizardWhereForm, FOIAWhatLocalForm, FOIAWhatStateForm, \
                       FOIAWhatFederalForm, FOIAWizard, TEMPLATES
from foia.models import FOIARequest, FOIADocument, FOIACommunication
from jurisdiction.models import Jurisdiction
from tags.models import Tag
from settings import STRIPE_SECRET_KEY, STRIPE_PUB_KEY

logger = logging.getLogger(__name__)
stripe.api_key = STRIPE_SECRET_KEY

def _foia_form_handler(request, foia, action):
    """Handle a form for a FOIA request - user to update a FOIA request"""
    # pylint: disable=R0912

    def default_form(data=None):
        """Make a default form to update a FOIA request"""
        if data:
            form = FOIARequestForm(data, instance=foia, request=request)
        else:
            form = FOIARequestForm(initial={'request': foia.first_request()},
                                   instance=foia, request=request)
        agency_pk = foia.agency and foia.agency.pk
        form.fields['agency'].queryset = \
            Agency.objects.filter(Q(jurisdiction=foia.jurisdiction, approved=True) |
                                  Q(jurisdiction=foia.jurisdiction, user=request.user) |
                                  Q(pk=agency_pk)) \
                          .order_by('name')
        return form

    if request.method == 'POST':
        status_dict = {'Submit Request': 'submitted', 'Save as Draft': 'started'}

        try:
            foia.status = status_dict[request.POST['submit']]

            form = default_form(request.POST)

            if form.is_valid():

                foia = form.save(commit=False)
                agency_name = request.POST.get('combo-name')
                new_agency = False
                if agency_name and (not foia.agency or agency_name != foia.agency.name):
                    # Use the combobox to create a new agency
                    foia.agency = Agency.objects.create(name=agency_name[:255],
                                                        slug=slugify(agency_name[:255]),
                                                        jurisdiction=foia.jurisdiction,
                                                        user=request.user, approved=False)
                    send_mail('[AGENCY] %s' % foia.agency.name,
                              render_to_string('foia/admin_agency.txt', {'agency': foia.agency}),
                              'info@muckrock.com', ['requests@muckrock.com'], fail_silently=False)
                    new_agency = True
                foia.slug = slugify(foia.title)
                foia_comm = foia.communications.all()[0]
                foia_comm.date = datetime.now()
                foia_comm.communication = form.cleaned_data['request']
                foia_comm.save()

                if request.POST['submit'] == 'Submit Request':
                    if request.user.get_profile().make_request():
                        foia.submit()
                        messages.success(request, 'Request succesfully submitted.')
                    else:
                        foia.status = 'started'
                        messages.error(request, 'You are out of requests for this month.  '
                            'Your request has been saved as a draft, please '
                            '<a href="%s">buy more requests</a> to submit it.'
                            % reverse('acct-buy-requests'))

                foia.save()

                if new_agency:
                    return HttpResponseRedirect(reverse('agency-update',
                        kwargs={'jurisdiction': foia.agency.jurisdiction.slug,
                                'slug': foia.agency.slug, 'idx': foia.agency.pk})
                                                + '?foia=%d' % foia.pk)
                else:
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

    jmodel = get_object_or_404(Jurisdiction, slug=jurisdiction)
    foia = get_object_or_404(FOIARequest, jurisdiction=jmodel, slug=slug, id=idx)

    if not foia.is_editable():
        messages.error(request, 'You may only edit non-submitted requests')
        return redirect(foia)
    if foia.user != request.user:
        messages.error(request, 'You may only edit your own requests')
        return redirect(foia)

    return _foia_form_handler(request, foia, 'Update')

def _foia_action(request, jurisdiction, slug, idx, action):
    """Generic helper for FOIA actions"""

    jmodel = get_object_or_404(Jurisdiction, slug=jurisdiction)
    foia = get_object_or_404(FOIARequest, jurisdiction=jmodel, slug=slug, pk=idx)
    form_class = action.form_class(request, foia)

    if action.must_own and foia.user != request.user:
        messages.error(request, 'You may only %s your own requests' % action.msg)
        return redirect(foia)

    for test, msg in action.tests:
        if not test(foia):
            messages.error(request, msg)
            return redirect(foia)

    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            action.form_actions(request, foia, form)
            return HttpResponseRedirect(action.return_url(request, foia))

    else:
        if isinstance(form_class, type) and issubclass(form_class, forms.ModelForm):
            form = form_class(instance=foia)
        else:
            form = form_class()

    context = action.extra_context(foia)
    context.update({'form': form, 'foia': foia, 'heading': action.heading, 'action': action.value})
    return render_to_response(action.template, context,
                              context_instance=RequestContext(request))

Action = namedtuple('Action', 'form_actions msg tests form_class return_url '
                              'heading value must_own template extra_context')

def _save_foia_comm(request, foia, form, action):
    """Save the FOI Communication"""
    if action == 'Admin Fix':
        foia.email = form.cleaned_data['email']
        foia.other_emails = form.cleaned_data['other_emails']
    FOIACommunication.objects.create(
            foia=foia, from_who=foia.user.get_full_name(), to_who=foia.get_to_who(),
            date=datetime.now(), response=False, full_html=False,
            communication=form.cleaned_data['comm'])
    foia.submit(appeal=(action == 'Appeal'))
    messages.success(request, '%s succesfully submitted.' % action)

@user_passes_test(lambda u: u.is_staff)
def admin_fix(request, jurisdiction, slug, idx):
    """Send an email from the requests auto email address"""

    action = Action(
        form_actions = lambda req, foia, form: _save_foia_comm(req, foia, form, 'Admin Fix'),
        msg = 'admin fix',
        tests = [],
        form_class = lambda r, f: FOIAAdminFixForm,
        return_url = lambda r, f: f.get_absolute_url(),
        heading = 'Email from Request Address',
        value = 'Submit',
        must_own = False,
        template = 'foia/foiarequest_action.html',
        extra_context = lambda f: {})
    return _foia_action(request, jurisdiction, slug, idx, action)

@login_required
def fix(request, jurisdiction, slug, idx):
    """Ammend a 'fix required' FOIA Request"""

    action = Action(
        form_actions = lambda req, foia, form: _save_foia_comm(req, foia, form, 'Fix'),
        msg = 'fix',
        tests = [(lambda f: f.is_fixable(), 'This request has not had a fix request')],
        form_class = lambda r, f: FOIAFixForm,
        return_url = lambda r, f: f.get_absolute_url(),
        heading = 'Fix FOIA Request',
        value = 'Fix',
        must_own = True,
        template = 'foia/foiarequest_action.html',
        extra_context = lambda f: {})
    return _foia_action(request, jurisdiction, slug, idx, action)

@login_required
def appeal(request, jurisdiction, slug, idx):
    """Appeal a rejected FOIA Request"""

    action = Action(
        form_actions = lambda req, foia, form: _save_foia_comm(req, foia, form, 'Appeal'),
        msg = 'appeal',
        tests = [(lambda f: f.is_appealable(), 'This request has not been rejected')],
        form_class = lambda r, f: FOIAAppealForm,
        return_url = lambda r, f: f.get_absolute_url(),
        heading = 'Appeal FOIA Request',
        value = 'Appeal',
        must_own = True,
        template = 'foia/foiarequest_action.html',
        extra_context = lambda f: {})
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
        form_class = lambda r, f: FOIAFlagForm,
        return_url = lambda r, f: f.get_absolute_url(),
        heading = 'Flag FOIA Request',
        value = 'Flag',
        must_own = False,
        template = 'foia/foiarequest_action.html',
        extra_context = lambda f: {})
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
        form_class = lambda r, f: FOIANoteForm,
        return_url = lambda r, f: f.get_absolute_url() + '#tabs-notes',
        heading = 'Add Note',
        value = 'Add',
        must_own = True,
        template = 'foia/foiarequest_action.html',
        extra_context = lambda f: {})
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
        form_class = lambda r, f: FOIADeleteForm,
        return_url = lambda r, f: reverse('foia-mylist', kwargs={'view': 'all'}),
        heading = 'Delete FOI Request',
        value = 'Delete',
        must_own = True,
        template = 'foia/foiarequest_action.html',
        extra_context = lambda f: {})
    return _foia_action(request, jurisdiction, slug, idx, action)

@login_required
def embargo(request, jurisdiction, slug, idx):
    """Change the embargo on a request"""

    def form_actions(_, foia, form):
        """Update the embargo date"""
        foia.embargo = form.cleaned_data.get('embargo')
        foia.date_embargo = form.cleaned_data.get('date_embargo')
        foia.save()
        logger.info('Embargo set by user for FOI Request %d %s to %s',
                    foia.pk, foia.title, foia.embargo)

    action = Action(
        form_actions = form_actions,
        msg = 'embargo',
        tests = [(lambda f: f.user.get_profile().can_embargo(),
                  'You may not embargo requests with your account type')],
        form_class = lambda r, f: FOIAEmbargoDateForm if f.date_embargo \
                                  else FOIAEmbargoForm,
        return_url = lambda r, f: f.get_absolute_url(),
        heading = 'Update the Embargo Date',
        value = 'Update',
        must_own = True,
        template = 'foia/foiarequest_action.html',
        extra_context = lambda f: {})
    return _foia_action(request, jurisdiction, slug, idx, action)

@login_required
def pay_request(request, jurisdiction, slug, idx):
    """Pay us through CC for the payment on a request"""
    # pylint: disable=W0142

    def form_actions(request, foia, form):
        """Pay for request"""
        try:
            amount = int(foia.price * 105)
            request.user.get_profile().pay(form, amount,
                                           'Charge for request %s' % foia.title)
            foia.status = 'processed'
            foia.save()

            send_mail('[PAYMENT] Freedom of Information Request: %s' % (foia.title),
                      render_to_string('foia/admin_payment.txt',
                                       {'request': foia, 'amount': amount / 100.0}),
                      'info@muckrock.com', ['requests@muckrock.com'], fail_silently=False)

            logger.info('%s has paid %0.2f for request %s' %
                        (request.user.username, amount/100, foia.title))
            messages.success(request, 'Your payment was successful')
            return HttpResponseRedirect(reverse('acct-my-profile'))
        except stripe.CardError as exc:
            messages.error(request, 'Payment error: %s' % exc)
            logger.error('Payment error: %s', exc, exc_info=sys.exc_info())
            return HttpResponseRedirect(reverse('foia-pay',
                kwargs={'jurisdiction': foia.jurisdiction.slug,
                        'slug': foia.slug,
                        'idx': foia.pk}))

    action = Action(
        form_actions = form_actions,
        msg = 'pay for',
        tests = [(lambda f: f.is_payable(),
                  'You may only pay for requests that require a payment')],
        form_class = lambda r, f: lambda *args, **kwargs: PaymentForm(request=r, *args, **kwargs),
        return_url = lambda r, f: f.get_absolute_url(),
        heading = 'Pay for Request',
        value = 'Pay',
        must_own = True,
        template = 'registration/cc.html',
        extra_context = lambda f: {'desc': 'You will be charged $%.2f for this request' %
                                   (f.price * Decimal('1.05')),
                                   'pub_key': STRIPE_PUB_KEY})
    return _foia_action(request, jurisdiction, slug, idx, action)

@login_required
def follow(request, jurisdiction, slug, idx):
    """Follow or unfollow a request"""

    jmodel = get_object_or_404(Jurisdiction, slug=jurisdiction)
    foia = get_object_or_404(FOIARequest, jurisdiction=jmodel, slug=slug, id=idx)

    if foia.user == request.user:
        messages.error(request, 'You may not follow your own request')
    else:
        if foia.followed_by.filter(user=request.user):
            foia.followed_by.remove(request.user.get_profile())
            messages.info(request, 'You are no longer following %s' % foia.title)
        else:
            foia.followed_by.add(request.user.get_profile())
            messages.info(request, 'You are now following %s.  You will be notified whenever it '
                                   'is updated.' % foia.title)

    return redirect(foia)

def _sort_requests(get, foia_requests, update_top=False):
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

    if update_top:
        return foia_requests.order_by('-updated', ob_field)
    else:
        return foia_requests.order_by(ob_field)

def _list(request, requests, extra_context=None, kwargs=None):
    """Helper function for creating list views"""
    # pylint: disable=W0142

    if not extra_context:
        extra_context = {}
    if not kwargs:
        kwargs = {}
    extra_context['title'] = 'FOI Requests'

    try:
        per_page = min(int(request.GET.get('per_page', 10)), 100)
    except ValueError:
        per_page = 10
    return list_detail.object_list(request, requests, paginate_by=per_page,
                                   extra_context=extra_context, **kwargs)

def list_(request):
    """List all viewable FOIA requests"""

    foia_requests = _sort_requests(request.GET, FOIARequest.objects.get_viewable(request.user))
    return _list(request, foia_requests)

def list_by_user(request, user_name):
    """List of all FOIA requests by a given user"""

    user = get_object_or_404(User, username=user_name)
    foia_requests = _sort_requests(request.GET,
                                   FOIARequest.objects.get_viewable(request.user).filter(user=user))

    return _list(request, foia_requests, extra_context={'subtitle': 'by %s' % user_name})

def list_by_tag(request, tag_slug):
    """List of all FOIA requests by a given user"""

    tag = get_object_or_404(Tag, slug=tag_slug)
    foia_requests = _sort_requests(request.GET,
                                   FOIARequest.objects.get_viewable(request.user).filter(tags=tag))

    return _list(request, foia_requests, extra_context={'subtitle': 'Tagged with "%s"' % tag.name})

@login_required
def my_list(request, view):
    """Views owned by current user"""
    # pylint: disable=E1103
    # pylint: disable=R0912

    def set_read_status(foia_pks, status):
        """Mark requests as read or unread"""
        for foia_pk in foia_pks:
            foia = FOIARequest.objects.get(pk=foia_pk, user=request.user)
            foia.updated = status
            foia.save()

    def handle_post():
        """Handle post data"""
        try:
            foia_pks = request.POST.getlist('foia')
            if request.POST.get('submit') == 'Add Tag':
                tag_pk = request.POST.get('tag')
                tag_name = Tag.normalize(request.POST.get('combo-name'))
                if tag_pk:
                    tag = Tag.objects.get(pk=tag_pk)
                elif tag_name:
                    tag, _ = Tag.objects.get_or_create(name=tag_name,
                                                       defaults={'user': request.user})
                if tag_pk or tag_name:
                    for foia_pk in foia_pks:
                        foia = FOIARequest.objects.get(pk=foia_pk, user=request.user)
                        foia.tags.add(tag)
            elif request.POST.get('submit') == 'Mark as Read':
                set_read_status(foia_pks, False)
            elif request.POST.get('submit') == 'Mark as Unread':
                set_read_status(foia_pks, True)
        except (FOIARequest.DoesNotExist, Tag.DoesNotExist):
            # bad foia or tag value passed in, just ignore
            pass

        return redirect('foia-mylist', view=view)

    if request.method == 'POST':
        return handle_post()

    unsorted = FOIARequest.objects.filter(user=request.user)
    if view == 'drafts':
        unsorted = unsorted.get_editable()
    elif view == 'action':
        unsorted = unsorted.filter(status__in=['fix', 'payment'])
    elif view == 'waiting':
        unsorted = unsorted.filter(status='processed')
    elif view == 'completed':
        unsorted = unsorted.filter(status__in=['rejected', 'no_docs', 'done', 'partial'])
    elif view != 'all':
        raise Http404()

    tag = request.GET.get('tag')
    if tag:
        unsorted = unsorted.filter(tags__slug=tag)
    tags = Tag.objects.filter(foiarequest__user=request.user).distinct()

    foia_requests = _sort_requests(request.GET, unsorted, update_top=True)

    return _list(request, foia_requests,
                 extra_context={'tags': tags, 'all_tags': Tag.objects.all()},
                 kwargs={'template_name': 'foia/foiarequest_mylist.html'})

@login_required
def list_following(request):
    """List of all FOIA requests the user is following"""

    foia_requests = _sort_requests(request.GET,
        FOIARequest.objects.get_viewable(request.user)
                           .filter(followed_by=request.user.get_profile()))

    return _list(request, foia_requests, extra_context={'subtitle': 'Following'})

def detail(request, jurisdiction, slug, idx):
    """Details of a single FOIA request"""

    jmodel = get_object_or_404(Jurisdiction, slug=jurisdiction)
    foia = get_object_or_404(FOIARequest, jurisdiction=jmodel, slug=slug, pk=idx)

    if not foia.is_viewable(request.user):
        raise Http404()

    if foia.updated and foia.user == request.user:
        foia.updated = False
        foia.save()

    if request.method == 'POST' and foia.user == request.user:
        foia.update_tags(request.POST['tags'])
        return redirect(foia)

    context = {'object': foia, 'all_tags': Tag.objects.all(),
               'communications': foia.get_communications(request.user)}
    context['past_due'] = foia.date_due < datetime.now().date() if foia.date_due else False
    context['actions'] = foia.actions(request.user)

    return render_to_response('foia/foiarequest_detail.html',
                              context,
                              context_instance=RequestContext(request))

def doc_cloud_detail(request, doc_id):
    """Details of a DocumentCloud document"""

    doc = get_object_or_404(FOIADocument, doc_id=doc_id)

    if not doc.is_viewable(request.user) or not doc.doc_id:
        raise Http404()

    return redirect(doc, permanant=True)

