"""
FOIA views for composing
"""

# Django
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.template.defaultfilters import slugify
from django.utils import timezone
from django.utils.encoding import smart_text
from django.views.generic import CreateView, FormView, UpdateView

# Standard Library
import re
from datetime import date
from math import ceil

# MuckRock
from muckrock.accounts.forms import BuyRequestForm
from muckrock.accounts.mixins import MiniregMixin
from muckrock.agency.models import Agency
from muckrock.foia.exceptions import InsufficientRequestsError
from muckrock.foia.forms import (
    ComposerForm,
    ContactInfoForm,
    MultiRequestDraftForm,
    MultiRequestForm,
    RequestDraftForm,
)
from muckrock.foia.models import FOIAComposer, FOIAMultiRequest, FOIARequest
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.task.models import MultiRequestTask
from muckrock.utils import new_action


def _submit_composer(request, composer):
    """Submit a composer with error handling"""
    try:
        composer.submit()
    except InsufficientRequestsError:
        messages.warning(request, 'You need to purchase more requests')
    else:
        messages.success(request, 'Request submitted')


class CreateComposer(MiniregMixin, CreateView):
    """Create a new composer"""
    # pylint: disable=attribute-defined-outside-init
    template_name = 'forms/foia/create.html'
    form_class = ComposerForm

    def get_initial(self):
        """Get initial data from clone, if there is one"""
        self.clone = False
        data = {}
        clone_pk = self.request.GET.get('clone')
        if clone_pk is not None:
            data.update(self._get_clone_data(clone_pk))
        agency_pks = self.request.GET.getlist('agency')
        agency_pks = [pk for pk in agency_pks if re.match('[0-9]+', pk)]
        if agency_pks:
            agencies = Agency.objects.filter(
                pk__in=agency_pks,
                status='approved',
            )
            data.update({'agencies': agencies})
        return data

    def _get_clone_data(self, clone_pk):
        """Get the intial data for a clone"""
        try:
            composer = get_object_or_404(FOIAComposer, pk=clone_pk)
        except ValueError:
            # non integer passed in as clone_pk
            return {}
        if not composer.has_perm(self.request.user, 'view'):
            raise Http404()
        initial_data = {
            'title': composer.title,
            'requested_docs': smart_text(composer.requested_docs),
            'agencies': composer.agencies.all(),
            'tags': composer.tags.all(),
            'parent': composer,
        }
        self.clone = True
        return initial_data

    def get_form_kwargs(self):
        """Add request to the form kwargs"""
        kwargs = super(CreateComposer, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        """Extra context"""
        context = super(CreateComposer, self).get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            foias_filed = (
                self.request.user.composers.exclude(status='started').count()
            )
            requests_left = {
                'regular': self.request.user.profile.num_requests,
                'monthly': self.request.user.profile.get_monthly_requests(),
            }
            org = self.request.user.profile.get_org()
            if org is not None:
                requests_left['org'] = org.get_requests()
        else:
            foias_filed = 0
            requests_left = {}
        context.update({
            'clone': self.clone,
            'featured': FOIARequest.objects.get_featured(self.request.user),
            'settings': settings,
            'foias_filed': foias_filed,
            'requests_left': requests_left,
            'buy_request_form': BuyRequestForm(user=self.request.user),
        })
        return context

    def form_valid(self, form):
        """Create the request"""
        if self.request.user.is_authenticated:
            user = self.request.user
        else:
            user = self.miniregister(
                form.cleaned_data['full_name'],
                form.cleaned_data['email'],
                form.cleaned_data.get('newsletter'),
            )
        if form.cleaned_data['action'] in ('save', 'submit'):
            composer = form.save(commit=False)
            composer.user = user
            composer.save()
            form.save_m2m()
        if form.cleaned_data['action'] == 'save':
            self.request.session['ga'] = 'request_drafted'
            messages.success(self.request, 'Request saved')
        elif form.cleaned_data['action'] == 'submit':
            _submit_composer(self.request, composer)
        return redirect(composer)


class UpdateComposer(UpdateView):
    """Update a composer"""
    # pylint: disable=attribute-defined-outside-init
    template_name = 'forms/foia/create.html'
    form_class = ComposerForm
    pk_url_kwarg = 'idx'
    context_object_name = 'composer'

    def get_queryset(self):
        """Restrict to composers you can view"""
        return FOIAComposer.objects.filter(
            status='started',
            user=self.request.user,
        )

    def get_form_kwargs(self):
        """Add request to the form kwargs"""
        kwargs = super(UpdateComposer, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        """Extra context"""
        context = super(UpdateComposer, self).get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            foias_filed = (
                self.request.user.composers.exclude(status='started').count()
            )
        else:
            foias_filed = 0
        context.update({
            'settings': settings,
            'foias_filed': foias_filed,
        })
        return context

    def post(self, request, *args, **kwargs):
        """Allow deletion regardless of form validation"""
        self.object = self.get_object()
        if (
            request.POST.get('action') == 'delete'
            and self.object.has_perm(request.user, 'delete')
        ):
            self.object.delete()
            messages.success(self.request, 'Draft deleted')
            return redirect('foia-mylist')
        return super(UpdateComposer, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        """Update the request"""
        if form.cleaned_data['action'] == 'save':
            composer = form.save()
            messages.success(self.request, 'Request saved')
        elif form.cleaned_data['action'] == 'submit':
            composer = form.save()
            _submit_composer(self.request, composer)
        return redirect(composer)


def _submit_request(request, foia, contact_info=None):
    """Submit request for user"""
    if not foia.user == request.user:
        messages.error(request, 'Only a request\'s owner may submit it.')
    elif not request.user.profile.make_request():
        error_msg = (
            'You do not have any requests remaining. '
            'Please purchase more requests and then resubmit.'
        )
        messages.error(request, error_msg)
    else:
        foia.process_attachments(request.user)
        foia.submit(contact_info=contact_info)
        if contact_info:
            foia.add_contact_info_note(request.user, contact_info)
        request.session['ga'] = 'request_submitted'
        messages.success(request, 'Your request was submitted.')
        new_action(request.user, 'submitted', target=foia)
    return redirect(foia)


class CreateRequest(FormView):
    """Create a new request"""
    template_name = 'forms/foia/create.html'
    form_class = ComposerForm

    def __init__(self, *args, **kwargs):
        super(CreateRequest, self).__init__(*args, **kwargs)
        self.clone = False
        self.parent = None

    def get_initial(self):
        """Get initial data from clone, if there is one"""
        clone_pk = self.request.GET.get('clone')
        if clone_pk is not None:
            return self._get_clone_data(clone_pk)
        agency_pk = self.request.GET.get('agency')
        if agency_pk is not None:
            try:
                agency = get_object_or_404(
                    Agency, pk=agency_pk, status='approved'
                )
            except ValueError:
                return {}
            initial_data = {'agency': agency}
            initial_data.update(
                self._get_jurisdiction_data(agency.jurisdiction)
            )
            return initial_data
        jurisdiction_pk = self.request.GET.get('jurisdiction')
        if jurisdiction_pk is not None:
            try:
                jurisdiction = get_object_or_404(
                    Jurisdiction, pk=jurisdiction_pk
                )
            except ValueError:
                return {}
            initial_data = self._get_jurisdiction_data(jurisdiction)
            return initial_data
        return {}

    def _get_clone_data(self, clone_pk):
        """Get the intial data for a clone"""
        try:
            foia = get_object_or_404(FOIARequest, pk=clone_pk)
        except ValueError:
            # non integer passed in as clone_pk
            return {}
        if not foia.has_perm(self.request.user, 'view'):
            raise Http404()
        initial_data = {
            'title': foia.title,
            'document': smart_text(foia.requested_docs),
            'agency': foia.agency,
        }
        initial_data.update(self._get_jurisdiction_data(foia.jurisdiction))
        self.clone = True
        self.parent = foia
        return initial_data

    def _get_jurisdiction_data(self, jurisdiction):
        """Get the jurisdiction data for the initial form"""
        initial_data = {}
        level = jurisdiction.level
        if level == 's':
            initial_data['state'] = jurisdiction
        elif level == 'l':
            initial_data['local'] = jurisdiction
        initial_data['jurisdiction'] = level
        return initial_data

    def get_form_kwargs(self):
        """Add request to the form kwargs"""
        kwargs = super(CreateRequest, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        """Extra context"""
        context = super(CreateRequest, self).get_context_data(**kwargs)
        context.update({
            'clone': self.clone,
            'featured': FOIARequest.objects.get_featured(self.request.user),
        })
        return context

    def form_valid(self, form):
        """Create the request"""
        foia = form.process(self.parent)
        self.request.session['ga'] = 'request_drafted'
        return redirect(foia)


@login_required
def draft_request(request, jurisdiction, jidx, slug, idx):
    """Edit a drafted FOIA Request"""
    # pylint: disable=too-many-locals
    foia = get_object_or_404(
        FOIARequest,
        agency__jurisdiction__slug=jurisdiction,
        agency__jurisdiction__pk=jidx,
        slug=slug,
        pk=idx,
    )
    #if not foia.is_editable():
    #messages.error(request, 'This is not a draft.')
    #return redirect(foia)
    if not foia.has_perm(request.user, 'change'):
        messages.error(
            request, 'You do not have permission to edit this draft.'
        )
        return redirect(foia)

    initial_data = {
        'title': foia.title,
        'request': foia.first_request(),
        'embargo': foia.embargo,
    }
    contact_info = {
        'portal': foia.agency.portal,
        'email': foia.agency.get_emails('primary', 'to').first(),
        'cc_emails': foia.agency.get_emails('primary', 'cc'),
        'fax': foia.agency.get_faxes('primary').first(),
        'address': foia.agency.get_addresses('primary').first(),
    }

    if request.method == 'POST':
        if request.POST.get('submit') == 'Delete':
            foia.delete()
            messages.success(request, 'The request was deleted.')
            return redirect('foia-mylist')
        form = RequestDraftForm(request.POST)
        contact_info_form = ContactInfoForm(request.POST, foia=foia)
        has_contact_perm = request.user.profile.is_advanced()
        use_contact_info = (
            has_contact_perm
            and request.POST.get('use_contact_information') == 'true'
        )
        contact_valid = contact_info_form.is_valid()
        if form.is_valid() and (not use_contact_info or contact_valid):
            data = form.cleaned_data
            foia.title = data['title']
            foia.slug = slugify(foia.title) or 'untitled'
            foia.embargo = data['embargo']
            has_embargo_perm = foia.has_perm(request.user, 'embargo')
            if foia.embargo and not has_embargo_perm:
                error_msg = 'Only Pro users may embargo their requests.'
                messages.error(request, error_msg)
                return redirect(foia)
            foia_comm = foia.last_comm()
            foia_comm.date = timezone.now()
            foia_comm.communication = smart_text(data['request'])
            foia_comm.save()
            foia.save(comment='draft edited')

            if request.POST.get('submit') == 'Save':
                messages.success(request, 'Your draft has been updated.')
            elif request.POST.get('submit') == 'Submit' and use_contact_info:
                _submit_request(request, foia, contact_info_form.cleaned_data)
            elif request.POST.get('submit') == 'Submit':
                _submit_request(request, foia)
            return redirect(
                'foia-detail',
                jurisdiction=foia.jurisdiction.slug,
                jidx=foia.jurisdiction.pk,
                slug=foia.slug,
                idx=foia.pk
            )
    else:
        form = RequestDraftForm(initial=initial_data)
        contact_info_form = ContactInfoForm(
            foia=foia,
            contact_info=contact_info,
        )

    context = {
        'action':
            'Draft',
        'form':
            form,
        'foia':
            foia,
        'remaining':
            request.user.profile.total_requests(),
        'foias_filed':
            request.user.composers.exclude(status='started').count(),
        'stripe_pk':
            settings.STRIPE_PUB_KEY,
        'sidebar_admin_url':
            reverse('admin:foia_foiarequest_change', args=(foia.pk,)),
        'MAX_ATTACHMENT_NUM':
            settings.MAX_ATTACHMENT_NUM,
        'MAX_ATTACHMENT_SIZE':
            settings.MAX_ATTACHMENT_SIZE,
        'ALLOWED_FILE_MIMES':
            settings.ALLOWED_FILE_MIMES,
        'ALLOWED_FILE_EXTS':
            settings.ALLOWED_FILE_EXTS,
        'AWS_STORAGE_BUCKET_NAME':
            settings.AWS_STORAGE_BUCKET_NAME,
        'AWS_ACCESS_KEY_ID':
            settings.AWS_ACCESS_KEY_ID,
        'contact_info':
            contact_info,
        'contact_info_form':
            contact_info_form,
    }

    return render(
        request,
        'forms/foia/draft.html',
        context,
    )


@login_required
def create_multirequest(request):
    """A view for composing multirequests"""
    # limit multirequest feature to Pro users
    if not request.user.profile.can_multirequest():
        messages.warning(request, 'Multirequesting is a Pro feature.')
        return redirect('accounts')

    if request.method == 'POST':
        form = MultiRequestForm(request.POST, user=request.user)
        if form.is_valid():
            multirequest = form.save(commit=False)
            multirequest.user = request.user
            multirequest.slug = slugify(multirequest.title)
            multirequest.status = 'started'
            multirequest.save()
            form.save_m2m()
            return redirect(multirequest)
    elif 'clone' in request.GET:
        try:
            multi = get_object_or_404(
                FOIAMultiRequest,
                user=request.user,
                pk=request.GET['clone'],
            )
        except ValueError:
            # non integer passed in as clone_pk
            initial_data = {}
        else:
            initial_data = {
                'title': multi.title,
                'requested_docs': smart_text(multi.requested_docs),
                'agencies': multi.agencies.all(),
                'parent': multi,
            }
        form = MultiRequestForm(user=request.user, initial=initial_data)
    else:
        form = MultiRequestForm(user=request.user)

    context = {'form': form}
    return render(
        request,
        'forms/foia/create_multirequest.html',
        context,
    )


@login_required
def draft_multirequest(request, slug, idx):
    """Update a started FOIA MultiRequest"""
    foia = get_object_or_404(FOIAMultiRequest, slug=slug, pk=idx)

    if foia.user != request.user:
        messages.error(request, 'You may only edit your own requests')
        return redirect('foia-mylist')
    if request.method == 'POST':
        if request.POST.get('submit') == 'Delete':
            foia.delete()
            messages.success(request, 'The request was deleted.')
            return redirect('foia-mylist')
        try:
            form = MultiRequestDraftForm(request.POST, instance=foia)
            if form.is_valid():
                foia = form.save(commit=False)
                foia.user = request.user
                foia.slug = slugify(foia.title) or 'untitled'
                foia.tags.set(*form.cleaned_data['tags'])
                foia.save()
                if request.POST['submit'] == 'Submit':
                    profile = request.user.profile
                    num_requests = len(foia.agencies.all())
                    request_count = profile.multiple_requests(num_requests)
                    if request_count['extra_requests']:
                        messages.warning(
                            request,
                            'You have not purchased enough requests.  '
                            'Please purchase more requests, then try '
                            'submitting again.',
                        )
                        return redirect(foia)
                    profile.num_requests -= request_count['reg_requests']
                    profile.monthly_requests -= request_count['monthly_requests'
                                                              ]
                    profile.save()
                    if profile.organization:
                        profile.organization.num_requests -= request_count[
                            'org_requests'
                        ]
                        profile.organization.save()
                    foia.num_reg_requests = request_count['reg_requests']
                    foia.num_monthly_requests = request_count['monthly_requests'
                                                              ]
                    foia.num_org_requests = request_count['org_requests']
                    foia.status = 'submitted'
                    foia.date_processing = date.today()
                    foia.save()
                    messages.success(
                        request, 'Your multi-request was submitted.'
                    )
                    MultiRequestTask.objects.create(multirequest=foia)
                    return redirect('foia-mylist')
                messages.success(request, 'Updates to this request were saved.')
                return redirect(foia)
        except KeyError:
            # bad post, not possible from web form
            form = MultiRequestDraftForm(instance=foia)
    else:
        form = MultiRequestDraftForm(instance=foia)

    profile = request.user.profile
    num_requests = len(foia.agencies.all())
    request_balance = profile.multiple_requests(num_requests)
    num_bundles = int(ceil(request_balance['extra_requests'] / 5.0))

    context = {
        'action': 'Draft',
        'form': form,
        'foia': foia,
        'profile': profile,
        'balance': request_balance,
        'bundles': num_bundles,
        'stripe_pk': settings.STRIPE_PUB_KEY
    }

    return render(
        request,
        'forms/foia/draft_multirequest.html',
        context,
    )
