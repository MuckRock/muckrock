"""
FOIA views for composing
"""

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string, get_template
from django.template import RequestContext, Context

from datetime import datetime
import logging
import stripe
from random import choice
import string

from muckrock.accounts.models import Profile
from muckrock.agency.models import Agency
from muckrock.foia.forms import \
    RequestForm, \
    RequestDraftForm, \
    MultiRequestForm, \
    MultiRequestDraftForm
from muckrock.foia.models import \
    FOIARequest, \
    FOIAMultiRequest, \
    FOIACommunication, \
    STATUS
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.settings import STRIPE_PUB_KEY, STRIPE_SECRET_KEY, MONTHLY_REQUESTS

# pylint: disable=R0901

logger = logging.getLogger(__name__)
stripe.api_key = STRIPE_SECRET_KEY
STATUS_NODRAFT = [st for st in STATUS if st != ('started', 'Draft')]

# HELPER FUNCTIONS

def get_foia(jurisdiction, jidx, slug, idx):
    """A helper function that gets and returns a FOIA object"""
    jmodel = get_object_or_404(Jurisdiction, slug=jurisdiction, pk=jidx)
    foia = get_object_or_404(FOIARequest, jurisdiction=jmodel, slug=slug, id=idx)
    return foia

def _make_comm(foia):
    """A helper function to compose the text of a communication"""
    template = get_template('text/foia/request.txt')
    context = Context({
        'document_request': foia.requested_docs,
        'jurisdiction': foia.jurisdiction,
        'user': foia.user
    })
    request_text = template.render(context).split('\n', 1)[1].strip()
    print request_text
    return request_text

def _make_new_agency(request, agency, jurisdiction):
    """Helper function to create new agency"""
    user = request.user if request.user.is_authenticated() else None
    agency = Agency.objects.create(
        name=agency[:255],
        slug=(slugify(agency[:255]) or 'untitled'),
        jurisdiction=jurisdiction,
        user=user,
        approved=False,
    )
    send_mail(
        '[AGENCY] %s' % agency.name,
        render_to_string(
            'text/foia/admin_agency.txt',
            {'agency': agency}
        ),
        'info@muckrock.com',
        ['requests@muckrock.com'],
        fail_silently=False
    )
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
    base_username = data['full_name'].replace(' ', '')
    username = base_username
    num = 1
    while User.objects.filter(username=username).exists():
        username = '%s%d' % (base_username, num)
        num += 1
    password = ''.join(choice(string.ascii_letters + string.digits) for _ in range(12))
    user = User.objects.create_user(username, data['email'], password)
    Profile.objects.create(
        user=user,
        acct_type='community',
        monthly_requests=MONTHLY_REQUESTS.get('community', 0),
        date_update=datetime.now()
    )
    link = user.get_profile().wrap_url(reverse('acct-change-pw'))
    send_mail('Welcome to MuckRock',
              render_to_string('text/user/welcome.txt',
                               {'data': data, 'pw': password,
                                'username': username, 'link': link}),
              'info@muckrock.com', [data['email']], fail_silently=False)
    if ' ' in data['full_name']:
        user.first_name, user.last_name = data['full_name'].rsplit(' ', 1)
    else:
        user.first_name = data['full_name']
    user.save()
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
    if not request.user.get_profile().make_request():
        error_msg = ('You do not have any requests remaining. '
                     'Please purchase more requests and then resubmit.')
        messages.error(request, error_msg)
    foia.submit()
    messages.success(request, 'Your request was submitted.')
    return redirect(foia)

# pylint: disable=unused-argument
def clone_request(request, jurisdiction, jidx, slug, idx):
    """A URL handler for cloning requests"""
    foia = get_foia(jurisdiction, jidx, slug, idx)
    return HttpResponseRedirect(reverse('foia-create') + '?clone=%s' % foia.pk)

def create_request(request):
    """A very important view for composing FOIA requests"""
    initial_data = {}
    clone = False
    parent = None
    if request.GET.get('clone', False):
        foia_pk = request.GET['clone']
        foia = get_object_or_404(FOIARequest, pk=foia_pk)
        initial_data = {
            'title': foia.title,
            'document': foia.requested_docs,
            'agency': foia.agency.name
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
    if request.method == 'POST':
        foia_request = _process_request_form(request)
        if foia_request:
            foia, foia_comm = _make_request(request, foia_request, parent)
            foia_comm.save()
            foia.save()
            return redirect(foia)
        else:
            # form is invalid
            form = RequestForm(request.POST, request=request)
    else:
        if clone:
            form = RequestForm(initial=initial_data, request=request)
        else:
            form = RequestForm(request=request)

    viewable = FOIARequest.objects.get_viewable(request.user)
    featured = viewable.filter(featured=True)

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
    if foia.user != request.user and not request.user.is_staff:
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
            if foia.embargo and not request.user.get_profile().can_embargo():
                error_msg = 'Only Pro users may embargo their requests.'
                messages.error(request, error_msg)
                return redirect(foia)
            foia_comm = foia.last_comm()
            foia_comm.date = datetime.now()
            foia_comm.communication = data['request']
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
        'stripe_pk': STRIPE_PUB_KEY
    }

    return render_to_response(
        'forms/foia/draft.html',
        context,
        context_instance=RequestContext(request)
    )

@login_required
def create_multirequest(request):
    """A view for composing multirequests"""
    if request.method == 'POST':
        form = MultiRequestForm(request.POST)
        if form.is_valid():
            print form.cleaned_data['agencies']
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
                    print foia.agencies.all()
                    profile = request.user.get_profile()
                    num_requests = len(foia.agencies.all())
                    request_count = profile.multiple_requests(num_requests)
                    if request_count['extra_requests']:
                        err_msg = 'You have not purchased enough requests.'
                        err_msg = 'Please purchase more requests, then try submitting again.'
                        messages.warning(request, err_msg)
                        return redirect(foia)
                    print request_count
                    print num_requests
                    profile.num_requests -= request_count['reg_requests']
                    profile.monthly_requests -= request_count['monthly_requests']
                    profile.save()
                    foia.status = 'submitted'
                    foia.save()
                    messages.success(request, 'Your multi-request was submitted.')
                    send_mail(
                        '[MULTI] Freedom of Information Request: %s' % (foia.title),
                        render_to_string(
                            'text/foia/multi_mail.txt',
                            {'request': foia}
                        ),
                        'info@muckrock.com',
                        ['requests@muckrock.com'],
                        fail_silently=False
                    )
                    return redirect('foia-mylist')
                messages.success(request, 'Updates to this request were saved.')
                return redirect(foia)
        except KeyError:
            # bad post, not possible from web form
            form = MultiRequestDraftForm(instance=foia)
    else:
        form = MultiRequestDraftForm(instance=foia)

    profile = request.user.get_profile()
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
        'stripe_pk': STRIPE_PUB_KEY
    }

    return render_to_response(
        'forms/foia/draft_multirequest.html',
        context,
        context_instance=RequestContext(request)
    )
