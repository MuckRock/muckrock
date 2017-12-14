"""
FOIA views for composing
"""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.template.defaultfilters import slugify
from django.utils.encoding import smart_text
from django.views.generic import FormView

from datetime import datetime, date
from math import ceil

from muckrock.foia.forms import (
    RequestForm,
    RequestDraftForm,
    MultiRequestForm,
    MultiRequestDraftForm,
    )
from muckrock.foia.models import (
    FOIARequest,
    FOIAMultiRequest,
    )
from muckrock.task.models import MultiRequestTask
from muckrock.utils import new_action


def _submit_request(request, foia):
    """Submit request for user"""
    if not foia.user == request.user:
        messages.error(request, 'Only a request\'s owner may submit it.')
    elif not request.user.profile.make_request():
        error_msg = ('You do not have any requests remaining. '
                     'Please purchase more requests and then resubmit.')
        messages.error(request, error_msg)
    else:
        foia.process_attachments(request.user)
        foia.submit()
        request.session['ga'] = 'request_submitted'
        messages.success(request, 'Your request was submitted.')
        new_action(request.user, 'submitted', target=foia)
    return redirect(foia)


def clone_request(request, jurisdiction, jidx, slug, idx):
    """A URL handler for cloning requests"""
    # pylint: disable=unused-argument
    foia = get_object_or_404(
            FOIARequest,
            jurisdiction__slug=jurisdiction,
            jurisdiction__pk=jidx,
            slug=slug,
            pk=idx,
            )
    return HttpResponseRedirect(reverse('foia-create') + '?clone=%s' % foia.pk)


class CreateRequest(FormView):
    """Create a new request"""
    template_name = 'forms/foia/create.html'
    form_class = RequestForm

    def __init__(self, *args, **kwargs):
        super(CreateRequest, self).__init__(*args, **kwargs)
        self.clone = False
        self.parent = None

    def get_initial(self):
        """Get initial data from clone, if there is one"""
        clone_pk = self.request.GET.get('clone')
        if clone_pk is None:
            return {}
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
        jurisdiction = foia.jurisdiction
        level = jurisdiction.level
        if level == 's':
            initial_data['state'] = jurisdiction
        elif level == 'l':
            initial_data['local'] = jurisdiction
        initial_data['jurisdiction'] = level
        self.clone = True
        self.parent = foia
        return initial_data

    def get_form_kwargs(self):
        """Add request to the form kwargs"""
        kwargs = super(CreateRequest, self).get_form_kwargs()
        kwargs.update({'request': self.request})
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
    foia = get_object_or_404(
            FOIARequest,
            jurisdiction__slug=jurisdiction,
            jurisdiction__pk=jidx,
            slug=slug,
            pk=idx,
            )
    if not foia.is_editable():
        messages.error(request, 'This is not a draft.')
        return redirect(foia)
    if not foia.has_perm(request.user, 'change'):
        messages.error(request, 'You may only edit your own drafts.')
        return redirect(foia)

    initial_data = {
        'title': foia.title,
        'request': foia.first_request(),
        'embargo': foia.embargo,
    }

    if request.method == 'POST':
        if request.POST.get('submit') == 'Delete':
            foia.delete()
            messages.success(request, 'The request was deleted.')
            return redirect('foia-mylist')
        form = RequestDraftForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            foia.title = data['title']
            foia.slug = slugify(foia.title) or 'untitled'
            foia.embargo = data['embargo']
            has_perm = foia.has_perm(request.user, 'embargo')
            if foia.embargo and not has_perm:
                error_msg = 'Only Pro users may embargo their requests.'
                messages.error(request, error_msg)
                return redirect(foia)
            foia_comm = foia.last_comm() # DEBUG
            foia_comm.date = datetime.now()
            foia_comm.communication = smart_text(data['request'])
            foia_comm.save()
            foia.save(comment='draft edited')

            if request.POST.get('submit') == 'Save':
                messages.success(request, 'Your draft has been updated.')
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

    context = {
        'action': 'Draft',
        'form': form,
        'foia': foia,
        'remaining': foia.user.profile.total_requests(),
        'stripe_pk': settings.STRIPE_PUB_KEY,
        'sidebar_admin_url': reverse('admin:foia_foiarequest_change', args=(foia.pk,)),
        'MAX_ATTACHMENT_NUM': settings.MAX_ATTACHMENT_NUM,
        'MAX_ATTACHMENT_SIZE': settings.MAX_ATTACHMENT_SIZE,
        'ALLOWED_FILE_MIMES': settings.ALLOWED_FILE_MIMES,
        'ALLOWED_FILE_EXTS': settings.ALLOWED_FILE_EXTS,
        'AWS_STORAGE_BUCKET_NAME': settings.AWS_STORAGE_BUCKET_NAME,
        'AWS_ACCESS_KEY_ID': settings.AWS_ACCESS_KEY_ID,
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
        form = MultiRequestForm(request.POST)
        if form.is_valid():
            multirequest = form.save(commit=False)
            multirequest.user = request.user
            multirequest.slug = slugify(multirequest.title)
            multirequest.status = 'started'
            multirequest.save()
            form.save_m2m()
            return redirect(multirequest)
    else:
        form = MultiRequestForm()

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
                    profile.monthly_requests -= request_count['monthly_requests']
                    profile.save()
                    if profile.organization:
                        profile.organization.num_requests -= request_count['org_requests']
                        profile.organization.save()
                    foia.num_reg_requests = request_count['reg_requests']
                    foia.num_monthly_requests = request_count['monthly_requests']
                    foia.num_org_requests = request_count['org_requests']
                    foia.status = 'submitted'
                    foia.date_processing = date.today()
                    foia.save()
                    messages.success(request, 'Your multi-request was submitted.')
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
    num_bundles = int(ceil(request_balance['extra_requests']/5.0))

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
