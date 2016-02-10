"""
FOIA views for composing
"""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string, get_template
from django.template import RequestContext, Context
from django.utils.encoding import smart_text

import actstream
from datetime import datetime, date
import json
import logging
from random import choice
import string

from muckrock.accounts.models import Profile
from muckrock.agency.models import Agency
from muckrock.foia.forms import (
    RequestForm,
    RequestDraftForm,
    MultiRequestForm,
    MultiRequestDraftForm,
    )
from muckrock.foia.models import (
    FOIARequest,
    FOIAMultiRequest,
    FOIACommunication,
    STATUS,
    )
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.task.models import NewAgencyTask, MultiRequestTask

# pylint: disable=too-many-ancestors

logger = logging.getLogger(__name__)
STATUS_NODRAFT = [st for st in STATUS if st != ('started', 'Draft')]

# HELPER FUNCTIONS

def get_foia(jurisdiction, jidx, slug, idx, select_related=None, prefetch_related=None):
    """A helper function that gets and returns a FOIA object"""
    # pylint: disable=too-many-arguments
    jmodel = get_object_or_404(Jurisdiction, slug=jurisdiction, pk=jidx)
    foia_qs = FOIARequest.objects.all()
    if select_related:
        foia_qs = foia_qs.select_related(*select_related)
    if prefetch_related:
        foia_qs = foia_qs.prefetch_related(*prefetch_related)
    foia = get_object_or_404(foia_qs, jurisdiction=jmodel, slug=slug, id=idx)
    return foia

def _make_comm(foia):
    """A helper function to compose the text of a communication"""
    template = get_template('text/foia/request.txt')
    context = Context({
        'document_request': smart_text(foia.requested_docs),
        'jurisdiction': foia.jurisdiction,
        'user': foia.user
    })
    request_text = template.render(context).split('\n', 1)[1].strip()
    return request_text

def _make_new_agency(request, agency, jurisdiction):
    """Helper function to create new agency"""
    user = request.user if request.user.is_authenticated() else None
    agency = Agency.objects.create(
        name=agency[:255],
        slug=(slugify(agency[:255]) or 'untitled'),
        jurisdiction=jurisdiction,
        user=user,
        status='pending',
    )
    NewAgencyTask.objects.create(
            assigned=user,
            user=user,
            agency=agency)
    return agency

def _make_request(request, foia_request, parent=None):
    """A helper function for creating request and comms objects"""
    foia = FOIARequest.objects.create(
        user=request.user,
        status='started',
        title=foia_request['title'],
        jurisdiction=foia_request['jurisdiction'],
        slug=slugify(foia_request['title']) or 'untitled',
        agency=foia_request['agency'],
        requested_docs=foia_request['document'],
        description=foia_request['document'],
        parent=parent
    )
    foia_comm = FOIACommunication.objects.create(
        foia=foia,
        from_who=request.user.get_full_name(),
        to_who=foia.get_to_who(),
        date=datetime.now(),
        response=False,
        full_html=False,
        communication=_make_comm(foia)
    )
    return foia, foia_comm

def _make_user(request, data):
    """Helper function to create a new user"""
    # create unique username thats at most 30 characters
    base_username = data['full_name'].replace(' ', '')[:30]
    username = base_username
    num = 1
    while User.objects.filter(username=username).exists():
        postfix = str(num)
        username = '%s%s' % (base_username[:30 - len(postfix)], postfix)
        num += 1
    # create random password
    password = ''.join(choice(string.ascii_letters + string.digits) for _ in range(12))
    # create a new user
    user = User.objects.create_user(username, data['email'], password)
    full_name = data['full_name'].strip()
    if ' ' in full_name:
        first_name, last_name = full_name.rsplit(' ', 1)
        user.first_name = first_name[:30]
        user.last_name = last_name[:30]
    else:
        user.first_name = full_name[:30]
    user.save()
    # create a new profile
    Profile.objects.create(
        user=user,
        acct_type='basic',
        monthly_requests=settings.MONTHLY_REQUESTS.get('basic', 0),
        date_update=datetime.now()
    )
    # send the new user a welcome email
    password_link = user.profile.wrap_url(reverse('acct-change-pw'))
    send_mail(
        'Welcome to MuckRock',
        render_to_string('text/user/welcome.txt', {
            'user': user,
            'password_link': password_link,
            'verification_link': user.profile.wrap_url(
                reverse('acct-verify-email'),
                key=user.profile.generate_confirmation_key())
        }),
        'info@muckrock.com',
        [data['email']],
        fail_silently=False
    )
    # login the new user
    user = authenticate(username=username, password=password)
    login(request, user)

def _process_request_form(request):
    """A helper function for getting info out of a request composer form"""
    form = RequestForm(request.POST, request=request)
    foia_request = {}
    if form.is_valid():
        data = form.cleaned_data
        if request.user.is_anonymous():
            _make_user(request, data)
        title = data['title']
        document = data['document']
        level = data['jurisdiction']
        if level == 'f':
            jurisdiction = Jurisdiction.objects.filter(level='f')[0]
        elif level == 's':
            jurisdiction = data['state']
        else:
            jurisdiction = data['local']
        agency_query = Agency.objects.filter(name=data['agency'], jurisdiction=jurisdiction)
        agency = agency_query[0] if agency_query \
                 else _make_new_agency(request, data['agency'], jurisdiction)
        foia_request.update({
            'title': title,
            'document': document,
            'jurisdiction': jurisdiction,
            'agency': agency,
        })
    return foia_request

def _submit_request(request, foia):
    """Submit request for user"""
    if not foia.user == request.user:
        messages.error(request, 'Only a request\'s owner may submit it.')
    if not request.user.profile.make_request():
        error_msg = ('You do not have any requests remaining. '
                     'Please purchase more requests and then resubmit.')
        messages.error(request, error_msg)
    foia.submit()
    request.session['ga'] = 'request_submitted'
    messages.success(request, 'Your request was submitted.')
    # generate action
    actstream.action.send(
        request.user,
        verb='submitted',
        action_object=foia,
        target=foia.agency
    )
    return redirect(foia)

def clone_request(request, jurisdiction, jidx, slug, idx):
    """A URL handler for cloning requests"""
    # pylint: disable=unused-argument
    foia = get_foia(jurisdiction, jidx, slug, idx)
    return HttpResponseRedirect(reverse('foia-create') + '?clone=%s' % foia.pk)

def create_request(request):
    """A very important view for composing FOIA requests"""
    # pylint: disable=too-many-locals
    # we should refactor this, its too long, and remove the pylint disable
    initial_data = {}
    clone = False
    parent = None
    try:
        foia_pk = request.GET['clone']
        foia = get_object_or_404(FOIARequest, pk=foia_pk)
        initial_data = {
            'title': foia.title,
            'document': smart_text(foia.requested_docs),
            'agency': foia.agency.name if foia.agency else ''
        }
        jurisdiction = foia.jurisdiction
        level = jurisdiction.level
        if level == 's':
            initial_data['state'] = jurisdiction
        elif level == 'l':
            initial_data['local'] = jurisdiction
        initial_data['jurisdiction'] = level
        clone = True
        parent = foia
    except (KeyError, ValueError):
        # KeyError if no clone was passed in
        # Value error if invalid clone is passed in
        pass
    if request.method == 'POST':
        foia_request = _process_request_form(request)
        if foia_request:
            foia, foia_comm = _make_request(request, foia_request, parent)
            foia_comm.save()
            foia.save()
            request.session['ga'] = 'request_drafted'
            return redirect(foia)
        else:
            # form is invalid
            # autocomplete blows up if you pass it a bad value in state
            # or local - not sure how this is happening, but am removing
            # non numeric values for these keys
            # this seems to technically be a bug in autocompletes rendering
            # should probably fix it there and submit a patch
            post = request.POST.copy()
            for chk_val in ['local', 'state']:
                try:
                    chk_val in post and int(post[chk_val])
                except (ValueError, TypeError):
                    del post[chk_val]
            form = RequestForm(post, request=request)
    else:
        if clone:
            form = RequestForm(initial=initial_data, request=request)
        else:
            form = RequestForm(request=request)

    featured = (FOIARequest.objects
            .get_viewable(request.user)
            .filter(featured=True)
            .select_related_view()
            .get_public_file_count())

    context = {
        'form': form,
        'clone': clone,
        'featured': featured
    }

    return render_to_response(
        'forms/foia/create.html',
        context,
        context_instance=RequestContext(request)
    )

@login_required
def draft_request(request, jurisdiction, jidx, slug, idx):
    """Edit a drafted FOIA Request"""
    foia = get_foia(jurisdiction, jidx, slug, idx)
    if not foia.is_editable():
        messages.error(request, 'This is not a draft.')
        return redirect(foia)
    if not foia.editable_by(request.user) and not request.user.is_staff:
        messages.error(request, 'You may only edit your own drafts.')
        return redirect(foia)

    initial_data = {
        'title': foia.title,
        'request': foia.first_request(),
        'embargo': foia.embargo
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
            if foia.embargo and not request.user.profile.can_embargo():
                error_msg = 'Only Pro users may embargo their requests.'
                messages.error(request, error_msg)
                return redirect(foia)
            foia_comm = foia.last_comm() # DEBUG
            foia_comm.date = datetime.now()
            foia_comm.communication = smart_text(data['request'])
            foia_comm.save()
            foia.save()
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
        'sidebar_admin_url': reverse('admin:foia_foiarequest_change', args=(foia.pk,))
    }

    return render_to_response(
        'forms/foia/draft.html',
        context,
        context_instance=RequestContext(request)
    )

@login_required
def create_multirequest(request):
    """A view for composing multirequests"""
    # limit multirequest feature to Pro users
    if not request.user.profile.can_multirequest():
        messages.warning(request, 'Multirequesting is a Pro feature.')
        return redirect('accounts')

    if request.method == 'GET' and request.is_ajax():
        agency_queries = request.GET.get('query', '').split(' ')
        agencies = {}
        matching_agencies = []
        # 1. get queryset
        # 2. transform into listM
        # 3. transform into set
        # 4. listN.append(set(listM))
        # 5. listN = list(reduce(set.intersection, listN))
        for agency_query in agency_queries:
            if len(agency_query) > 2:
                matching_agencies.append(set(list(Agency.objects.filter(approved=True).filter(
                    Q(name__icontains=agency_query)|
                    Q(aliases__icontains=agency_query)|
                    Q(jurisdiction__name__icontains=agency_query)|
                    Q(types__name__exact=agency_query)
                ))))
        try:
            matching_agencies = list(reduce(set.intersection, matching_agencies))
        except TypeError:
            matching_agencies = []
        for agency in matching_agencies:
            agencies[agency.name] = agency.id
        return HttpResponse(json.dumps(agencies), content_type='application/json')

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
    return render_to_response(
        'forms/foia/create_multirequest.html',
        context,
        context_instance=RequestContext(request)
    )

@login_required
def draft_multirequest(request, slug, idx):
    """Update a started FOIA MultiRequest"""
    from math import ceil

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
                        err_msg = 'You have not purchased enough requests.'
                        err_msg = 'Please purchase more requests, then try submitting again.'
                        messages.warning(request, err_msg)
                        return redirect(foia)
                    profile.num_requests -= request_count['reg_requests']
                    profile.monthly_requests -= request_count['monthly_requests']
                    profile.save()
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

    return render_to_response(
        'forms/foia/draft_multirequest.html',
        context,
        context_instance=RequestContext(request)
    )
