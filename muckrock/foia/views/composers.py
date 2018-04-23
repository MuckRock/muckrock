"""
FOIA views for composing
"""

# Django
from celery import current_app
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.encoding import smart_text
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, UpdateView

# Standard Library
import re
from datetime import timedelta

# MuckRock
from muckrock.accounts.mixins import BuyRequestsMixin, MiniregMixin
from muckrock.agency.models import Agency
from muckrock.foia.constants import COMPOSER_EDIT_DELAY
from muckrock.foia.exceptions import InsufficientRequestsError
from muckrock.foia.forms import BaseComposerForm, ComposerForm, ContactInfoForm
from muckrock.foia.models import FOIAComposer, FOIARequest


class GenericComposer(BuyRequestsMixin):
    """Shared functionality between create and update composer views"""
    template_name = 'forms/foia/create.html'
    form_class = ComposerForm
    context_object_name = 'composer'

    def get_form_kwargs(self):
        """Add request to the form kwargs"""
        kwargs = super(GenericComposer, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        if len(self.request.POST.getlist('agencies')) == 1:
            # pass the agency for contact info form
            try:
                kwargs['agency'] = Agency.objects.get(
                    pk=self.request.POST.get('agencies')
                )
            except (Agency.DoesNotExist, ValueError):
                # ValueError for new agency format
                pass
        return kwargs

    def get_context_data(self, **kwargs):
        """Extra context"""
        context = super(GenericComposer, self).get_context_data(**kwargs)
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
            context['sidebar_admin_url'] = reverse(
                'admin:foia_foiacomposer_change',
                args=(self.object.pk,),
            )
        else:
            foias_filed = 0
            requests_left = {}
        context.update({
            'settings': settings,
            'foias_filed': foias_filed,
            'requests_left': requests_left,
        })
        return context

    def _submit_composer(self, composer, form):
        """Submit a composer"""
        # pylint: disable=not-an-iterable
        if form.cleaned_data.get('num_requests', 0) > 0:
            self.buy_requests(form)
        if (
            form.cleaned_data.get('use_contact_information')
            and self.request.user.profile.is_advanced()
            and len(composer.agencies.all()) == 1
        ):
            contact_info = {
                k: form.cleaned_data.get(k)
                for k in ContactInfoForm.base_fields
            }
        else:
            contact_info = None
        try:
            composer.submit(contact_info)
        except InsufficientRequestsError:
            messages.warning(self.request, 'You need to purchase more requests')
        else:
            messages.success(self.request, 'Request submitted')
            warning = self._proxy_warnings(composer)
            if warning:
                messages.warning(self.request, warning)

    def _proxy_warnings(self, composer):
        """Check composer's agencies for proxy status"""
        proxies = {'missing': 0, 'non-missing': 0}
        for agency in composer.agencies.all():
            proxy_info = agency.get_proxy_info()
            if proxy_info['proxy'] and proxy_info['missing_proxy']:
                proxies['missing'] += 1
            elif proxy_info['proxy'] and not proxy_info['missing_proxy']:
                proxies['non-missing'] += 1
        if proxies['missing'] and proxies['non-missing']:
            return (
                'Some of the agencies you are requesting from require '
                'requestors to be in-state citizens.  We will file these '
                'with volunteer filers in states in which we have a '
                'volunteer available.  If we do not have a volunteer '
                'available, your request will be filed once we find a '
                'suitable volunteer.'
            )
        elif proxies['missing']:
            return (
                'Some of the agencies you are requesting from require '
                'requestors to be in-state citizens.  We do not currently '
                'have a citizen proxy requestor on file for these '
                'agencies, but will attempt to find one to submit these '
                'requests on your behalf.'
            )
        elif proxies['non-missing']:
            return (
                'Some of the agencies you are requesting from require '
                'requestors to be in-state citizens.  These requests will '
                'be filed in the name of one of our volunteer files for '
                'these states.'
            )
        else:
            return ''


class CreateComposer(MiniregMixin, GenericComposer, CreateView):
    """Create a new composer"""

    # pylint: disable=attribute-defined-outside-init

    def get_initial(self):
        """Get initial data from clone, if there is one"""
        self.clone = None
        # set title to blank, as if we create a new empty draft, it will
        # set the title to 'Untitled'
        data = {'title': ''}
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
            'edited_boilerplate': composer.edited_boilerplate,
            'parent': composer,
        }
        self.clone = composer
        return initial_data

    def get_context_data(self, **kwargs):
        """Extra context"""
        # if user is authenticated, save an empty draft to the database
        # so that autosaving and file uploading will work
        if self.request.user.is_authenticated:
            self.object = (
                FOIAComposer.objects.get_or_create_draft(
                    user=self.request.user
                )
            )
        context = super(CreateComposer, self).get_context_data(**kwargs)
        context.update({
            'clone': self.clone,
            'featured': FOIARequest.objects.get_featured(self.request.user),
        })
        return context

    def form_valid(self, form):
        """Create the request"""
        if self.request.user.is_authenticated:
            user = self.request.user
        else:
            user = self.miniregister(
                form.cleaned_data['register_full_name'],
                form.cleaned_data['register_email'],
                form.cleaned_data.get('register_newsletter'),
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
            self._submit_composer(composer, form)
        return redirect(composer)


class UpdateComposer(LoginRequiredMixin, GenericComposer, UpdateView):
    """Update a composer"""
    # pylint: disable=attribute-defined-outside-init
    pk_url_kwarg = 'idx'

    def get_queryset(self):
        """Restrict to composers you can view"""
        if self.request.method == 'POST':
            # can only post draft requests
            return FOIAComposer.objects.filter(
                status='started',
                user=self.request.user,
            )
        else:
            # can get recently submitted requests also, which will convert them
            # back to drafts
            # allow all composer's here - we don't want to 404 on non-drafts
            return FOIAComposer.objects.filter(user=self.request.user)

    def get_object(self, queryset=None):
        """Convert object back to draft if it has been submitted recently"""
        composer = super(UpdateComposer, self).get_object(queryset)
        can_revoke = (
            composer.delayed_id != '' and composer.datetime_submitted <
            timezone.now() + timedelta(seconds=COMPOSER_EDIT_DELAY)
        )
        if composer.status == 'submitted' and can_revoke:
            current_app.control.revoke(composer.delayed_id)
            composer.status = 'started'
            composer.delayed_id = ''
            composer.datetime_submitted = None
            composer.return_requests()
            composer.save()
            messages.warning(
                self.request,
                'This request\'s submission has been cancelled.  You may now '
                'edit it and submit it again when ready',
            )
        return composer

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

    def get(self, request, *args, **kwargs):
        """Redirect if this composer is not a draft"""
        self.object = self.get_object()
        if self.object.status != 'started':
            messages.warning(
                self.request, 'This request can no longer be updated.'
            )
            return redirect(self.object)
        else:
            return self.render_to_response(self.get_context_data())

    def form_valid(self, form):
        """Update the request"""
        if form.cleaned_data['action'] == 'save':
            composer = form.save()
            self.request.session['ga'] = 'request_drafted'
            messages.success(self.request, 'Request saved')
        elif form.cleaned_data['action'] == 'submit':
            composer = form.save()
            self._submit_composer(composer, form)
        return redirect(composer)


@login_required
@require_POST
def autosave(request, idx):
    """Save the composer via AJAX"""
    composer = get_object_or_404(
        FOIAComposer,
        pk=idx,
        status='started',
        user=request.user,
    )
    data = request.POST.copy()
    # we are always just saving
    data['action'] = 'save'
    form = BaseComposerForm(data, instance=composer, user=request.user)
    if form.is_valid():
        form.save()
        return HttpResponse('OK')
    else:
        return HttpResponseBadRequest(form.errors.as_json())
