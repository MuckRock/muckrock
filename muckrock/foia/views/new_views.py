from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.formtools.wizard.views import SessionWizardView
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string, get_template
from django.template import RequestContext
from django.utils import simplejson

from muckrock.accounts.models import Profile
from muckrock.agency.models import Agency
from muckrock.foia.new_forms import RequestForm, RequestUpdateForm
from muckrock.foia.models import FOIARequest, FOIACommunication
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.settings import MONTHLY_REQUESTS

from datetime import datetime
from random import random, randint, choice
import logging
import string

logger = logging.getLogger(__name__)

def _compose_comm(user, document, jurisdiction):
        intro = 'This is a request under the Freedom of Information Act.'
        waiver = ('I also request that, if appropriate, fees be waived as I '
                  'believe this request is in the public interest. '
                  'The requested documents  will be made available to the ' 
                  'general public free of charge as part of the public ' 
                  'information service at MuckRock.com, processed by a ' 
                  'representative of the news media/press and is made in the ' 
                  ' process of news gathering and not for commercial usage.')
        delay = '20 business days'
        
        if jurisdiction.get_intro():
            intro = jurisdiction.get_intro()                
        if jurisdiction.get_waiver():
            waiver = jurisdiction.get_waiver()
        if jurisdiction.get_days():
            delay = jurisdiction.get_days()
        
        prepend = [
            'To Whom it May Concern:',
            intro + ' I hereby request the following records:'
        ]
        append = [
            waiver,
            ('In the event that fees cannot be waived, I would be '
            'grateful if you would inform me of the total charges in '     
            'advance of fulfilling my request. I would prefer the '
            'request filled electronically, by e-mail attachment if ' 
            'available or CD-ROM if not.'),
            ('Thank you in advance for your anticipated cooperation in '
            'this matter. I look forward to receiving your response to ' 
            'this request within %s, as the statute requires.' % delay ),
            'Sincerely, ' + user.get_full_name()
        ]
        return '\n\n'.join(prepend + [document] + append)

def _make_request(request, foia):
        title = foia['title']
        document = foia['document']
        slug = slugify(title) or 'untitled'
        jurisdiction = foia['jurisdiction']
        agency = foia['agency']
        is_new_agency = foia['is_new_agency']
        is_clone = foia['is_clone']
        if is_new_agency:
            agency = Agency.objects.create(
                name=agency[:255],
                slug=(slugify(agency[:255]) or 'untitled'),
                jurisdiction=jurisdiction,
                user=request.user,
                approved=False
            )
            send_mail(
                '[AGENCY] %s' % foia.agency.name,
                render_to_string(
                    'foia/admin_agency.txt',
                    {'agency': foia.agency}
                ),
                'info@muckrock.com',
                ['requests@muckrock.com'],
                fail_silently=False
            )
        foia = FOIARequest.objects.create(
            user=request.user,
            status='started',
            title=title,
            jurisdiction=jurisdiction,
            slug=slug,
            agency=agency,
            requested_docs=document,
            description=document
        )
        FOIACommunication.objects.create(
            foia=foia,
            from_who=request.user.get_full_name(),             
            to_who=foia.get_to_who(),
            date=datetime.now(),
            response=False,
            full_html=False,
            communication=_compose_comm(request.user, document, jurisdiction)
        )
        foia_comm = foia.communications.all()[0]
        foia_comm.date = datetime.now()
        return foia, foia_comm, is_new_agency

def _make_user(request, data):
    """Helper function to create a new user"""
    username = 'MuckRocker%d' % randint(1, 10000)
    # XXX verify this is unique
    password = ''.join(choice(string.ascii_letters + string.digits) for _ in range(12))
    user = User.objects.create_user(username, data['email'], password)
    # XXX email the user their account details
    if ' ' in data['full_name']:
        user.first_name, user.last_name = data['full_name'].rsplit(' ', 1)
    else:
        user.first_name = data['full_name']
    user.save()
    user = authenticate(username=username, password=password)
    Profile.objects.create(user=user,
                           acct_type='community',
                           monthly_requests=MONTHLY_REQUESTS.get('community', 0),
                           date_update=datetime.now())
    login(request, user)
    
@login_required
def update_request(request, jurisdiction, jidx, slug, idx):
    """Update a started FOIA Request"""
    
    jmodel = get_object_or_404(Jurisdiction, slug=jurisdiction, pk=jidx)
    foia = get_object_or_404(FOIARequest, jurisdiction=jmodel, slug=slug, id=idx)
    
    if not foia.is_editable():
        messages.error(request, 'You may only edit non-submitted requests.')
        return redirect(foia)
    if foia.user != request.user:
        messages.error(request, 'You may only edit your own requests.')
        return redirect(foia)
    
    initial_data = {
        'title': foia.title,
        'request': foia.first_request(),
        'agency': foia.agency.name,
        'embargo': foia.embargo
    }
    
    if request.method == 'POST':
        form = RequestUpdateForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            foia.title = data['title']
            foia.slug = slugify(foia.title) or 'untitled'
            foia.embargo = data['embargo']
            foia_comm = foia.communications.all()[0]
            foia_comm.date = datetime.now()
            foia_comm.communication = data['request']
            foia_comm.save()
            agency_query = Agency.objects.filter(name=data['agency'])
            if agency_query:
                agency = agency_query[0]
                foia.agency = agency
                is_new_agency = False
            else:
                agency = data['agency']
                foia.agency = Agency.objects.create(
                    name=agency[:255],
                    slug=(slugify(agency[:255]) or 'untitled'),
                    jurisdiction=jurisdiction,
                    user=request.user,
                    approved=False
                )
                send_mail(
                    '[AGENCY] %s' % foia.agency.name,
                    render_to_string(
                        'foia/admin_agency.txt',
                        {'agency': foia.agency}
                    ),
                    'info@muckrock.com',
                    ['requests@muckrock.com'],
                    fail_silently=False
                )
                is_new_agency = True
            
            foia.save
            
            messages.success(request, 'The request has been updated.')
            return redirect(foia)
        else:
            return redirect(foia)
    else:
        form = RequestUpdateForm(initial=initial_data)
    
    return render_to_response(
        'forms/foia.html',
        {'form': form, 'action': 'Update'},
        context_instance=RequestContext(request)
    )

def clone_request(request, jurisdiction, jidx, slug, idx):
    jmodel = get_object_or_404(Jurisdiction, slug=jurisdiction, pk=jidx)
    foia = get_object_or_404(FOIARequest, jurisdiction=jmodel, slug=slug, id=idx)
    return HttpResponseRedirect(reverse('foia-create') + '?clone=%s' % foia.pk)

def create_request(request):
    initial_data = {}
    clone = False
    if request.GET.get('clone', False):
        foia_pk = request.GET['clone']
        foia = get_object_or_404(FOIARequest, pk=foia_pk)
        clone = True
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

    if request.GET.get('j_id', False):
        j_id = request.GET['j_id']
        if j_id == 'f':
            j_id = Jurisdiction.objects.filter(level=j_id)[0].id
        agencies = Agency.objects.filter(jurisdiction=j_id, approved=True).order_by('name')
        results  = [agency.name for agency in agencies]
        json = simplejson.dumps(results)
        return HttpResponse(json, mimetype='application/json')
    
    if request.method == 'POST':
        form = RequestForm(request.POST, request=request)
        if form.is_valid():
            data = form.cleaned_data
            title = data['title']
            document = data['document']
            level = data['jurisdiction']
            if level == 'f':
                jurisdiction = Jurisdiction.objects.filter(level='f')[0]
            elif level == 's':
                jurisdiction = data['state']
            else:
                jurisdiction = data['local']
            agency_query = Agency.objects.filter(name=data['agency'])
            if agency_query:
                agency = agency_query[0]
                is_new_agency = False
            else:
                agency = data['agency']
                is_new_agency = True

            if request.user.is_anonymous():
                _make_user(request, data)
        
            foia_request = {
                'title': title,
                'document': document,
                'jurisdiction': jurisdiction,
                'agency': agency,
                'is_new_agency': is_new_agency,
                'is_clone': clone
            }
    
            foia, foia_comm, is_new_agency = _make_request(request, foia_request)
            foia_comm.save()
            foia.save()
            '''
            if is_new_agency:
                args = {
                    'jurisdiction': foia.agency.jurisdiction.slug,
                    'jidx': foia.agency.jurisdiction.pk,
                    'slug': foia.agency.slug,
                    'idx': foia.agency.pk
                }
                return HttpResponseRedirect(
                    reverse('agency-update', kwargs=args) + \
                    '?foia=%s' % foia.pk
                )
            else:
                return redirect(foia)
            messages.error(request, 'Sorry, something went wrong. We have top men on it.')
            '''
            return redirect(foia)
    else:
        if clone:
            form = RequestForm(initial=initial_data, request=request)
        else:
            form = RequestForm(request=request)
    
    context = { 'form': form, 'clone': clone }
    
    return render_to_response('forms/create.html', context, 
                              context_instance=RequestContext(request))

