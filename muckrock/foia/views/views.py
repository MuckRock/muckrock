"""
Views for the FOIA application
"""

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
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

from datetime import datetime
import logging
import stripe

from muckrock.agency.models import Agency
from muckrock.accounts.forms import PaymentForm
from muckrock.foia.codes import CODES
from muckrock.foia.forms import FOIARequestForm, \
                                FOIAWizardWhereForm, \
                                FOIAWhatLocalForm, \
                                FOIAWhatStateForm, \
                                FOIAWhatFederalForm, \
                                FOIAMultipleSubmitForm, \
                                AgencyConfirmForm, \
                                FOIAMultiRequestForm, \
                                TEMPLATES
from muckrock.foia.models import FOIARequest, FOIAMultiRequest, STATUS
from muckrock.foia.views.comms import move_comm, delete_comm, save_foia_comm, resend_comm
from muckrock.foia.wizards import SubmitMultipleWizard, FOIAWizard
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.settings import STRIPE_SECRET_KEY
from muckrock.tags.models import Tag
from muckrock.qanda.models import Question
from muckrock.sidebar.models import Sidebar
from muckrock.views import class_view_decorator

# pylint: disable=R0901

logger = logging.getLogger(__name__)
stripe.api_key = STRIPE_SECRET_KEY
STATUS_NODRAFT = [st for st in STATUS if st != ('started', 'Draft')]

def _foia_form_handler(request, foia, action):
    """Handle a form for a FOIA request - user to update a FOIA request"""
    # pylint: disable=R0912

    def default_form(data=None):
        """Make a default form to update a FOIA request"""
        agency_pk = foia.agency and foia.agency.pk
        if not data:
            data = initial={'request': foia.first_request()}
        form = FOIARequestForm(data, instance=foia, request=request)
        
        form.fields['agency'].queryset = Agency.objects.filter(
            Q(jurisdiction=foia.jurisdiction, approved=True) |
            Q(jurisdiction=foia.jurisdiction, user=request.user) |
            Q(pk=agency_pk)
        ).order_by('name')
        return form

    if request.method == 'POST':
        
        if request.POST.get('submit') == 'Delete':
            foia.delete()
            messages.info(request, 'Request succesfully deleted')
            return HttpResponseRedirect(
                reverse('foia-mylist', kwargs={'view': 'all'})
            )
        
        status_dict = {
            'Submit Request': 'submitted',
            'Save as Draft': 'started',
            'Submit to Multiple Agencies': 'started'
        }
        
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

                if new_agency:
                    return HttpResponseRedirect(reverse('agency-update',
                        kwargs={'jurisdiction': foia.agency.jurisdiction.slug,
                                'jidx': foia.agency.jurisdiction.pk,
                                'slug': foia.agency.slug, 'idx': foia.agency.pk})
                                                + '?foia=%d' % foia.pk)
                else:
                    return redirect(foia)

        except KeyError:
            # bad post, not possible from web form
            form = default_form()
    else:
        form = default_form()

    return render_to_response('foia/foiarequest_form.html',
                              {'form': form, 'action': action},
                              context_instance=RequestContext(request))

@login_required
def multiple(request, **kwargs):
    """Submit a multi agency request using the wizard"""

    multi_forms = [
        ('submit', FOIAMultipleSubmitForm),
        ('agency', AgencyConfirmForm),
        ('pay', PaymentForm),
        ('nopay', forms.Form),
        ]

    def payment_req(wizard):
        """Is a payment form required?"""
        data = wizard.get_cleaned_data_for_step('agency')
        if data:
            agencies = data.get('agencies')
        if data and agencies:
            num_requests = agencies.count()
            extra_context = wizard.request.user.get_profile().multiple_requests(num_requests)
            return extra_context['extra_requests'] > 0
        return False

    condition_dict = {
        'pay': payment_req,
        'nopay': lambda wizard: not payment_req(wizard),
    }

    return SubmitMultipleWizard.as_view(multi_forms,
        condition_dict=condition_dict)(request, **kwargs)

@login_required
def create(request):
    """Create a new foia request using the wizard"""

    def display_what_form(levels):
        """Display which 'What Form'"""
        def condition(wizard):
            """For condition dict"""
            cleaned_data = wizard.get_cleaned_data_for_step('FOIAWizardWhereForm') or {}
            return cleaned_data.get('level') in levels
        return condition

    def display_template_form(template):
        """Display which 'Template Form'"""
        def condition(wizard):
            """For condition dict"""
            cleaned_data = wizard.get_cleaned_data_for_step('FOIAWizardWhereForm') or {}
            level = cleaned_data.get('level', '').capitalize()
            if level == 'Multi':
                level = 'Local'
            what_form = 'FOIAWhat%sForm' % level
            cleaned_data = wizard.get_cleaned_data_for_step(what_form) or {}
            return cleaned_data.get('template') == template
        return condition

    # collect all the forms so that the wizard can access them
    wizard_forms = [(form.__name__, form) for form in
        [FOIAWizardWhereForm, FOIAWhatLocalForm, FOIAWhatStateForm, FOIAWhatFederalForm]]
    # if the form has no base fields, it requires no additional information and should not be
    # included in the wizard ie pet data
    wizard_forms += [(t.__name__, t) for t in TEMPLATES.values() if t.base_fields]

    condition_dict = {
        'FOIAWhatLocalForm':   display_what_form(('local', 'multi')),
        'FOIAWhatStateForm':   display_what_form(('state',)),
        'FOIAWhatFederalForm': display_what_form(('federal',)),
    }
    condition_dict.update(dict((t.__name__, display_template_form(tslug))
                               for tslug, t in TEMPLATES.iteritems()))

    return FOIAWizard.as_view(wizard_forms, condition_dict=condition_dict)(request)

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

@login_required
def multirequest_update(request, slug, idx):
    """Update a started FOIA MultiRequest"""

    foia = get_object_or_404(FOIAMultiRequest, slug=slug, pk=idx)

    if foia.user != request.user:
        messages.error(request, 'You may only edit your own requests')
        return HttpResponseRedirect(reverse('foia-mylist', kwargs={'view': 'all'}))

    if request.method == 'POST':
        if request.POST.get('submit') == 'Delete':
            foia.delete()
            messages.info(request, 'Request succesfully deleted')
            return HttpResponseRedirect(reverse('foia-mylist', kwargs={'view': 'all'}))

        try:
            form = FOIAMultiRequestForm(request.POST, instance=foia)

            if form.is_valid():

                foia = form.save(commit=False)
                foia.user = request.user
                foia.slug = slugify(foia.title) or 'untitled'
                foia.save()

                if request.POST['submit'] == 'Submit Requests':
                    return HttpResponseRedirect(reverse('foia-multi',
                                                        kwargs={'idx': foia.pk, 'slug': foia.slug}))

                messages.success(request, 'Request has been saved')
                return redirect(foia)

        except KeyError:
            # bad post, not possible from web form
            form = FOIAMultiRequestForm(instance=foia)
    else:
        form = FOIAMultiRequestForm(instance=foia)

    return render_to_response('foia/foiamultirequest_form.html', {'form': form, 'foia': foia},
                              context_instance=RequestContext(request))


class ListBase(ListView):
    """Base list view for other list views to inherit from"""

    def sort_requests(self, foia_requests, update_top=False):
        """Sorts the FOIA requests"""
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
        query = FOIARequest.objects.get_viewable(self.request.user)
        return self.sort_requests(query)

class ListByUser(ListBase):
    """List of all FOIA requests by a given user"""
    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs['user_name'])
        query = FOIARequest.objects.get_viewable(self.request.user)
        return self.sort_requests(query.filter(user=user))
    def get_context_data(self, **kwargs):
        context = super(ListByUser, self).get_context_data(**kwargs)
        context['subtitle'] = 'by %s' % self.kwargs['user_name']
        return context

class ListByAgency(ListBase):
    """List of all FOIA requests by a given agency"""
    def get_agency(self):
        agency = get_object_or_404(
            Agency,
            slug=self.kwargs['agency'],
            pk=self.kwargs['idx']
        )
        return agency
    def get_queryset(self):
        agency = get_agency(self)
        query = FOIARequest.objects.get_viewable(self.request.user)
        return self.sort_requests(query.filter(agency=agency))
    def get_context_data(self, **kwargs):
        agency = get_agency(self)
        context = super(ListByAgency, self).get_context_data(**kwargs)
        context['subtitle'] = 'for %s' % agency.name
        return context

class ListByJurisdiction(ListBase):
    """List of all FOIA requests by a given jurisdiction"""
    def get_jurisdiction(self):
        agency = get_object_or_404(
            Jurisdiction,
            slug=self.kwargs['jurisdiction'],
            pk=self.kwargs['idx']
        )
    def get_queryset(self):
        jurisdiction = get_jurisdiction(self)
        query = FOIARequest.objects.get_viewable(self.request.user)
        return self.sort_requests(query.filter(jurisdiction=jurisdiction))
    def get_context_data(self, **kwargs):
        jurisdiction = get_jurisdiction(self)
        context = super(ListByJurisdiction, self).get_context_data(**kwargs)
        context['subtitle'] = 'for %s' % jurisdiction.name
        return context

class ListByTag(ListBase):
    """List of all FOIA requests by a given tag"""
    def get_tag(self):
        tag = get_object_or_404(
            Tag,
            slug=self.kwargs['tag_slug'],
        )
    def get_queryset(self):
        tag = get_tag(self)
        query = FOIARequest.objects.get_viewable(self.request.user)
        return self.sort_requests(query.filter(tags=tag))
    def get_context_data(self, **kwargs):
        tag = get_tag(self)
        context = super(ListByTag, self).get_context_data(**kwargs)
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
            # Allow multi requests to have tags
            _ = post.getlist('multi')
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

    def merge_requests(self, foia_requests, multi_requests):
        """Merges the sorted FOIA requests with the multi requests"""

        get = self.request.GET

        order = get.get('order', 'desc')
        field = get.get('field', 'date_submitted')

        updated_foia_requests = [f for f in foia_requests if f.updated]
        other_foia_requests = [f for f in foia_requests if not f.updated]

        if field == 'title':
            both = list(other_foia_requests) + list(multi_requests)
            both.sort(key=lambda x: x.title, reverse=(order != 'asc'))
            both = updated_foia_requests + both
        elif field == 'status':
            both = list(other_foia_requests) + list(multi_requests)
            both.sort(key=lambda x: x.status, reverse=(order != 'asc'))
            both = updated_foia_requests + both
        elif order == 'asc':
            both = list(updated_foia_requests) + list(other_foia_requests) + list(multi_requests)
        else:
            both = list(updated_foia_requests) + list(multi_requests) + list(other_foia_requests)

        return both

    def get_queryset(self):
        """Get FOIAs for this view"""
        unsorted = FOIARequest.objects.filter(user=self.request.user)
        multis = FOIAMultiRequest.objects.filter(user=self.request.user)
        view = self.kwargs.get('view', 'all')
        if view == 'drafts':
            unsorted = unsorted.get_editable()
        elif view == 'action':
            unsorted = unsorted.filter(status__in=['fix', 'payment'])
        elif view == 'waiting':
            unsorted = unsorted.filter(status__in=['ack', 'processed'])
        elif view == 'completed':
            unsorted = unsorted.filter(status__in=['rejected', 'no_docs', 'done', 'partial'])
        elif view != 'all':
            raise Http404()

        tag = self.request.GET.get('tag')
        if tag:
            unsorted = unsorted.filter(tags__slug=tag)
            multis = multis.filter(tags__slug=tag)

        sorted_requests = self.sort_requests(unsorted, update_top=True)
        if view in ['drafts', 'all']:
            sorted_requests = self.merge_requests(sorted_requests, multis)
        return sorted_requests

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
    """Details of a single FOIA request as well
    as handling post actions for the request"""

    model = FOIARequest
    context_object_name = 'foia'

    def get_object(self, queryset=None):
        """Get the FOIA Request"""
        # pylint: disable=W0613
        jmodel = get_object_or_404(
            Jurisdiction,
            slug=self.kwargs['jurisdiction'],
            pk=self.kwargs['jidx']
        )
        foia = get_object_or_404(
            FOIARequest,
            jurisdiction=jmodel,
            slug=self.kwargs['slug'],
            pk=self.kwargs['idx']
        )
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
        context['choices'] = STATUS if self.request.user.is_staff else STATUS_NODRAFT
        return context

    def post(self, request, **kwargs):
        """Handle form submissions"""
        foia = self.get_object()
        actions = {
            'status': self._status,
            'tags': self._tags,
            'Follow Up': self._follow_up,
            'Get Advice': self._question,
            'Problem?': self._flag,
            'Appeal': self._appeal,
            'move_comm': move_comm,
            'delete_comm': delete_comm,
            'resend_comm': resend_comm,
        }
        try:
            return actions[request.POST['action']](request, foia)
        except KeyError: # if submitting form from web page improperly
            return redirect(foia)

    def _tags(self, request, foia):
        """Handle updating tags"""
        if foia.user == request.user:
            foia.update_tags(request.POST.get('tags'))
        return redirect(foia)

    def _status(self, request, foia):
        """Handle updating status"""
        status = request.POST.get('status')
        old_status = foia.get_status_display()
        if foia.status not in ['started', 'submitted'] and ((foia.user == request.user and status in [s for s, _ in STATUS_NODRAFT]) or (request.user.is_staff and status in [s for s, _ in STATUS])):
            foia.status = status
            foia.save()
            
            subject = '%s changed the status of "%s" to %s' % (
                request.user.username,
                foia.title,
                foia.get_status_display()
            )
            args = {
                'request': foia,
                'old_status': old_status,
                'user': request.user
            }
            send_mail(
                subject,
                render_to_string('foia/status_change.txt', args),
                'info@muckrock.com',
                ['requests@muckrock.com'],
                fail_silently=False
            )
        return redirect(foia)

    def _follow_up(self, request, foia):
        """Handle submitting follow ups"""
        if foia.user == request.user and foia.status != 'started':
            save_foia_comm(
                request,
                foia,
                foia.user.get_full_name(),
                request.POST.get('text'),
                'Follow up succesfully sent'
            )
        return redirect(foia)

    def _question(self, request, foia):
        """Handle asking a question"""
        if foia.user == request.user:
            title = 'Question about request: %s' % foia.title
            question = Question.objects.create(
                user=request.user,
                title=title,
                slug=slugify(title),
                foia=foia,
                question=request.POST.get('text'),
                date=datetime.now()
            )
            messages.success(request, 'Question succesfully posted')
            question.notify_new()
            return redirect(question)
        else:
            error_msg = 'You may only ask questions about your own requests.'
            messages.error(request, msg)
            return redirect(foia)

    def _flag(self, request, foia):
        """Allow a user to notify us of a problem with the request"""
        if request.user.is_authenticated():
            args = {
                'request': foia,
                'user': request.user,
                'reason': request.POST.get('text')
            }
            send_mail(
                '[FLAG] Freedom of Information Request: %s' % foia.title,
                render_to_string('foia/flag.txt', args),
                'info@muckrock.com',
                ['requests@muckrock.com'],
                fail_silently=False
            )
            messages.info(request, 'Problem succesfully reported')
        return redirect(foia)

    def _appeal(self, request, foia):
        """Handle submitting an appeal"""
        if foia.user == request.user and foia.is_appealable():
            save_foia_comm(
                request,
                foia,
                foia.user.get_full_name(),
                request.POST.get('text'),
                'Appeal succesfully sent',
                appeal=True
            )
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

@user_passes_test(lambda u: u.is_staff)
def acronyms(request):
    """A page with all the acronyms explained"""
    status_dict = dict(STATUS)
    codes = [(acro, name, status_dict.get(status, ''), desc)
             for acro, (name, status, desc) in CODES.iteritems()]
    codes.sort()
    return render_to_response(
        'foia/acronyms.html',
        {'codes': codes},
        context_instance=RequestContext(request)
    )