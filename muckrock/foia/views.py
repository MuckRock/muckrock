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
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from collections import namedtuple
from datetime import datetime
from decimal import Decimal
from urllib import urlencode
import logging
import stripe
import sys

from muckrock.agency.models import Agency
from muckrock.accounts.forms import PaymentForm
from muckrock.foia.forms import FOIARequestForm, FOIADeleteForm, FOIAAdminFixForm, FOIANoteForm, \
                                FOIAEmbargoForm, FOIAEmbargoDateForm, FOIAWizardWhereForm, \
                                FOIAWhatLocalForm, FOIAWhatStateForm, FOIAWhatFederalForm, \
                                FOIAWizard, FOIAFileFormSet, FOIAMultipleSubmitForm, \
                                AgencyConfirmForm, TEMPLATES
from muckrock.foia.models import FOIARequest, FOIACommunication, FOIAFile
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.settings import STRIPE_SECRET_KEY, STRIPE_PUB_KEY
from muckrock.tags.models import Tag
from muckrock.qanda.models import Question
from muckrock.views import class_view_decorator

# pylint: disable=R0901

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
        status_dict = {'Submit Request': 'submitted', 'Save as Draft': 'started',
                       'Submit to Multiple Agencies': 'started'}

        if request.POST.get('submit') == 'Delete':
            foia.delete()
            messages.info(request, 'Request succesfully deleted')
            return HttpResponseRedirect(reverse('foia-mylist', kwargs={'view': 'all'}))

        try:
            foia.status = status_dict[request.POST['submit']]

            form = default_form(request.POST)

            if form.is_valid():

                foia = form.save(commit=False)
                agency_name = request.POST.get('combo-name')
                new_agency = False
                if agency_name and (not foia.agency or agency_name != foia.agency.name):
                    # Use the combobox to create a new agency
                    foia.agency = Agency.objects.create(
                        name=agency_name[:255],
                        slug=(slugify(agency_name[:255]) or 'untitled'),
                        jurisdiction=foia.jurisdiction,
                        user=request.user, approved=False)
                    send_mail('[AGENCY] %s' % foia.agency.name,
                              render_to_string('foia/admin_agency.txt', {'agency': foia.agency}),
                              'info@muckrock.com', ['requests@muckrock.com'], fail_silently=False)
                    new_agency = True
                foia.slug = slugify(foia.title) or 'untitled'
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

                if request.POST['submit'] == 'Submit to Multiple Agencies':
                    return HttpResponseRedirect(reverse('foia-submit-multiple',
                                                        kwargs={'foia': foia.pk}))

                if new_agency:
                    return HttpResponseRedirect(reverse('agency-update',
                        kwargs={'jurisdiction': foia.agency.jurisdiction.slug,
                                'jidx': foia.agency.jurisdiction.pk,
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

@user_passes_test(lambda u: u.is_staff)
def submit_multiple(request, foia):
    """Submit a request to multiple agencies"""

    if request.method == 'POST':
        form = FOIAMultipleSubmitForm(request.POST)
        if form.is_valid():
            url = reverse('foia-confirm-multiple', kwargs={'foia': foia})
            url += '?' + urlencode([(k, v.pk) for k, v in form.cleaned_data.iteritems() if v])
            return HttpResponseRedirect(url)
    else:
        form = FOIAMultipleSubmitForm()

    return render_to_response('foia/foiarequest_submit_multiple.html', {'form': form},
                              context_instance=RequestContext(request))

@user_passes_test(lambda u: u.is_staff)
def confirm_multiple(request, foia):
    """Display the selected agencies and allow the user to confirm them"""
    # pylint: disable=R0914

    agency_type = request.GET.get('agency_type')
    jurisdiction = request.GET.get('jurisdiction')

    agencies = Agency.objects.all()
    if agency_type:
        agencies = agencies.filter(types__id=agency_type)
    if jurisdiction:
        agencies = agencies.filter(Q(jurisdiction=jurisdiction) |
                                   Q(jurisdiction__parent=jurisdiction))
    choices = [(a.pk, a.name) for a in agencies]

    if request.method == 'POST':
        form = AgencyConfirmForm(request.POST, choices=choices)
        if form.is_valid():
            foia = FOIARequest.objects.get(pk=foia)
            foia_comm = foia.communications.all()[0]
            if request.POST.get('submit') == 'Confirm':
                for agency_pk in form.cleaned_data['agencies']:
                    # make a copy of the foia (and its communication) for each agency
                    agency = Agency.objects.get(pk=agency_pk)
                    title = '%s (%s)' % (foia.title, agency.name)
                    new_foia = FOIARequest.objects.create(user=foia.user, status='started',
                                                          title=title, slug=foia.slug,
                                                          jurisdiction=agency.jurisdiction,
                                                          agency=agency)
                    FOIACommunication.objects.create(
                            foia=new_foia, from_who=foia_comm.from_who, to_who=foia_comm.to_who,
                            date=datetime.now(), response=False, full_html=False,
                            communication=foia_comm.communication)

                    new_foia.submit()
                messages.success(request, 'Request has been submitted to selected agencies')
            else:
                messages.info(request, 'Multiple agency submit has been cancelled')

        return redirect(foia)

    default = [pk for pk, _ in choices]
    form = AgencyConfirmForm(choices=choices, initial={'agencies': default})

    return render_to_response('foia/foiarequest_confirm_multiple.html', {'form': form},
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
def update(request, jurisdiction, jidx, slug, idx):
    """Update a started FOIA Request"""

    jmodel = get_object_or_404(Jurisdiction, slug=jurisdiction, pk=jidx)
    foia = get_object_or_404(FOIARequest, jurisdiction=jmodel, slug=slug, id=idx)

    if not foia.is_editable():
        messages.error(request, 'You may only edit non-submitted requests')
        return redirect(foia)
    if foia.user != request.user:
        messages.error(request, 'You may only edit your own requests')
        return redirect(foia)

    return _foia_form_handler(request, foia, 'Update')

def _foia_action(request, jurisdiction, jidx, slug, idx, action):
    """Generic helper for FOIA actions"""
    # pylint: disable=R0913

    jmodel = get_object_or_404(Jurisdiction, slug=jurisdiction, pk=jidx)
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

def _save_foia_comm(request, foia, from_who, comm, message, formset=None, appeal=False):
    """Save the FOI Communication"""
    # pylint: disable=R0913
    comm = FOIACommunication.objects.create(
            foia=foia, from_who=from_who, to_who=foia.get_to_who(),
            date=datetime.now(), response=False, full_html=False,
            communication=comm)
    if formset is not None:
        foia_files = formset.save(commit=False)
        for foia_file in foia_files:
            foia_file.comm = comm
            foia_file.title = foia_file.name()
            foia_file.date = comm.date
            foia_file.save()
    foia.submit(appeal=appeal)
    messages.success(request, message)

@user_passes_test(lambda u: u.is_staff)
def admin_fix(request, jurisdiction, jidx, slug, idx):
    """Send an email from the requests auto email address"""

    jmodel = get_object_or_404(Jurisdiction, slug=jurisdiction, pk=jidx)
    foia = get_object_or_404(FOIARequest, jurisdiction=jmodel, slug=slug, pk=idx)

    if request.method == 'POST':
        form = FOIAAdminFixForm(request.POST)
        formset = FOIAFileFormSet(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            if form.cleaned_data['email']:
                foia.email = form.cleaned_data['email']
            if form.cleaned_data['other_emails']:
                foia.other_emails = form.cleaned_data['other_emails']
            if form.cleaned_data['from_email']:
                from_who = form.cleaned_data['from_email']
            else:
                from_who = foia.user.get_full_name()
            _save_foia_comm(request, foia, from_who, form.cleaned_data['comm'],
                            'Admin Fix submitted', formset)
            return redirect(foia)
    else:
        form = FOIAAdminFixForm(instance=foia)
        formset = FOIAFileFormSet(queryset=FOIAFile.objects.none())

    context = {'form': form, 'foia': foia, 'heading': 'Email from Request Address',
               'formset': formset, 'action': 'Submit'}
    return render_to_response('foia/foiarequest_action.html', context,
                              context_instance=RequestContext(request))

@login_required
def note(request, jurisdiction, jidx, slug, idx):
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
    return _foia_action(request, jurisdiction, jidx, slug, idx, action)

@login_required
def delete(request, jurisdiction, jidx, slug, idx):
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
    return _foia_action(request, jurisdiction, jidx, slug, idx, action)

@login_required
def embargo(request, jurisdiction, jidx, slug, idx):
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
    return _foia_action(request, jurisdiction, jidx, slug, idx, action)

@login_required
def pay_request(request, jurisdiction, jidx, slug, idx):
    """Pay us through CC for the payment on a request"""
    # pylint: disable=W0142

    def form_actions(request, foia, form):
        """Pay for request"""
        try:
            amount = int(foia.price * 105)
            request.user.get_profile().pay(form, amount,
                                           'Charge for request: %s %s' % (foia.title, foia.pk))
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
    return _foia_action(request, jurisdiction, jidx, slug, idx, action)

@login_required
def follow(request, jurisdiction, jidx, slug, idx):
    """Follow or unfollow a request"""

    jmodel = get_object_or_404(Jurisdiction, slug=jurisdiction, pk=jidx)
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


class ListBase(ListView):
    """Base list view for other list views to inherit from"""

    def sort_requests(self, foia_requests, update_top=False):
        """Sort's the FOIA requests"""

        get = self.request.GET

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

    def get_paginate_by(self, queryset):
        try:
            return min(int(self.request.GET.get('per_page', 10)), 100)
        except ValueError:
            return 10

    def get_context_data(self, **kwargs):
        context = super(ListBase, self).get_context_data(**kwargs)
        context['title'] = 'FOI Requests'
        return context


class List(ListBase):
    """List all viewable FOIA Requests"""

    def get_queryset(self):
        return self.sort_requests(FOIARequest.objects.get_viewable(self.request.user))


class ListByUser(ListBase):
    """List of all FOIA requests by a given user"""

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs['user_name'])
        return self.sort_requests(FOIARequest.objects.get_viewable(self.request.user)
                                                     .filter(user=user))

    def get_context_data(self, **kwargs):
        context = super(ListByUser, self).get_context_data(**kwargs)
        context['subtitle'] = 'by %s' % self.kwargs['user_name']
        return context


class ListByTag(ListBase):
    """List of all FOIA requests by a given tag"""

    def get_queryset(self):
        tag = get_object_or_404(Tag, slug=self.kwargs['tag_slug'])
        return self.sort_requests(FOIARequest.objects.get_viewable(self.request.user)
                                                     .filter(tags=tag))

    def get_context_data(self, **kwargs):
        context = super(ListByTag, self).get_context_data(**kwargs)
        tag = get_object_or_404(Tag, slug=self.kwargs['tag_slug'])
        context['subtitle'] = 'Tagged with %s' % tag.name
        return context


@class_view_decorator(login_required)
class MyList(ListBase):
    """View requests owned by current user"""
    template_name = 'foia/foiarequest_mylist.html'

    def set_read_status(self, foia_pks, status):
        """Mark requests as read or unread"""
        for foia_pk in foia_pks:
            foia = FOIARequest.objects.get(pk=foia_pk, user=self.request.user)
            foia.updated = status
            foia.save()

    def post(self, request, view='all'):
        """Handle updating tags"""
        try:
            post = request.POST
            foia_pks = post.getlist('foia')
            if post.get('submit') == 'Add Tag':
                tag_pk = post.get('tag')
                tag_name = Tag.normalize(post.get('combo-name'))
                if tag_pk:
                    tag = Tag.objects.get(pk=tag_pk)
                elif tag_name:
                    tag, _ = Tag.objects.get_or_create(name=tag_name,
                                                       defaults={'user': request.user})
                if tag_pk or tag_name:
                    for foia_pk in foia_pks:
                        foia = FOIARequest.objects.get(pk=foia_pk, user=request.user)
                        foia.tags.add(tag)
            elif post.get('submit') == 'Mark as Read':
                self.set_read_status(foia_pks, False)
            elif post.get('submit') == 'Mark as Unread':
                self.set_read_status(foia_pks, True)
        except (FOIARequest.DoesNotExist, Tag.DoesNotExist):
            # bad foia or tag value passed in, just ignore
            pass

        return redirect('foia-mylist', view=view)

    def get_queryset(self):
        """Get FOIAs for this view"""
        unsorted = FOIARequest.objects.filter(user=self.request.user)
        view = self.kwargs.get('view', 'all')
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

        tag = self.request.GET.get('tag')
        if tag:
            unsorted = unsorted.filter(tags__slug=tag)

        return self.sort_requests(unsorted, update_top=True)

    def get_context_data(self, **kwargs):
        context = super(MyList, self).get_context_data(**kwargs)
        context['tags'] = Tag.objects.filter(foiarequest__user=self.request.user).distinct()
        context['all_tags'] = Tag.objects.all()
        return context


@class_view_decorator(login_required)
class ListFollowing(ListBase):
    """List of all FOIA requests the user is following"""

    def get_queryset(self):
        """Get FOIAs for this view"""
        return self.sort_requests(
            FOIARequest.objects.get_viewable(self.request.user)
                               .filter(followed_by=self.request.user.get_profile()))

    def get_context_data(self, **kwargs):
        context = super(ListFollowing, self).get_context_data(**kwargs)
        context['subtitle'] = 'Following'
        return context


class Detail(DetailView):
    """Details of a single FOIA request as well as handling post actions for the request"""

    model = FOIARequest
    context_object_name = 'foia'

    def get_object(self, queryset=None):
        """Get the FOIA Request"""
        # pylint: disable=W0613
        jmodel = get_object_or_404(Jurisdiction, slug=self.kwargs['jurisdiction'],
                                                 pk=self.kwargs['jidx'])
        foia = get_object_or_404(FOIARequest, jurisdiction=jmodel, slug=self.kwargs['slug'],
                                              pk=self.kwargs['idx'])

        if not foia.is_viewable(self.request.user):
            raise Http404()

        if foia.updated and foia.user == self.request.user:
            foia.updated = False
            foia.save()

        return foia

    def get_context_data(self, **kwargs):
        """Add extra context data"""
        context = super(Detail, self).get_context_data(**kwargs)
        foia = context['foia']
        context['all_tags'] = Tag.objects.all()
        context['past_due'] = foia.date_due < datetime.now().date() if foia.date_due else False
        context['actions'] = foia.actions(self.request.user)
        return context

    def post(self, request, **kwargs):
        """Handle form submissions"""
        # pylint: disable=W0613

        foia = self.get_object()

        actions = {
            'Submit': self._tags,
            'Follow Up': self._follow_up,
            'Get Advice': self._question,
            'Problem?': self._flag,
            'Appeal': self._appeal,
        }

        try:
            return actions[request.POST['submit']](request, foia)
        except KeyError:
            # should never happen if submitting form from web page properly
            return redirect(foia)

    def _tags(self, request, foia):
        """Handle updating tags"""
        # pylint: disable=R0201
        if foia.user == request.user:
            foia.update_tags(request.POST.get('tags'))
        return redirect(foia)

    def _follow_up(self, request, foia):
        """Handle submitting follow ups"""
        # pylint: disable=R0201
        if foia.user == request.user:
            _save_foia_comm(request, foia, foia.user.get_full_name(), request.POST.get('text'),
                            'Follow up succesfully sent')
        return redirect(foia)

    def _question(self, request, foia):
        """Handle asking a question"""
        # pylint: disable=R0201
        if foia.user == request.user:
            title = 'Question about request: %s' % foia.title
            question = Question.objects.create(
                user=request.user, title=title, slug=slugify(title), foia=foia,
                question=request.POST.get('text'), date=datetime.now())
            messages.success(request, 'Question succesfully posted')
            return redirect(question)
        else:
            return redirect(foia)

    def _flag(self, request, foia):
        """Allow a user to notify us of a problem with the request"""
        # pylint: disable=R0201
        if request.user.is_authenticated():
            send_mail('[FLAG] Freedom of Information Request: %s' % foia.title,
                      render_to_string('foia/flag.txt',
                                       {'request': foia, 'user': request.user,
                                        'reason': request.POST.get('text')}),
                      'info@muckrock.com', ['requests@muckrock.com'], fail_silently=False)
            messages.info(request, 'Problem succesfully reported')
        return redirect(foia)

    def _appeal(self, request, foia):
        """Handle submitting an appeal"""
        # pylint: disable=R0201
        if foia.user == request.user and foia.is_appealable():
            _save_foia_comm(request, foia, foia.user.get_full_name(), request.POST.get('text'),
                            'Appeal succesfully sent', appeal=True)
        return redirect(foia)


def redirect_old(request, jurisdiction, slug, idx, action):
    """Redirect old urls to new urls"""
    # pylint: disable=W0612
    # pylint: disable=W0613

    # some jurisdiction slugs changed, just ignore the jurisdiction slug passed in
    foia = get_object_or_404(FOIARequest, pk=idx)
    jurisdiction = foia.jurisdiction.slug
    jidx = foia.jurisdiction.pk

    if action == 'view':
        return redirect('/foi/%(jurisdiction)s-%(jidx)s/%(slug)s-%(idx)s/' % locals())

    if action == 'admin-fix':
        action = 'admin_fix'
    
    return redirect('/foi/%(jurisdiction)s-%(jidx)s/%(slug)s-%(idx)s/%(action)s/' % locals())
