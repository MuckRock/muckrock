from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.formtools.wizard.views import SessionWizardView
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, redirect
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string, get_template
from django.template import RequestContext
from django.utils import simplejson

from muckrock.agency.models import Agency
from muckrock.foia.new_forms import RequestForm
from muckrock.foia.models import FOIARequest, FOIACommunication
from muckrock.jurisdiction.models import Jurisdiction

import pickle
from datetime import datetime
import logging
logger = logging.getLogger(__name__)

SESSION_NAME = 'foia_request'

def create_request(request):
    initial_data = {}
    clone = False
    if request.session.get(SESSION_NAME, False):
        clone = True
        print request.session[SESSION_NAME]

        # TODO drop session data into initial_data
        
    if request.method == 'GET':
        results = []
        if request.GET.has_key(u'jID'):
            j_id = request.GET[u'jID']
            agencies = Agency.objects.filter(jurisdiction=jID).order_by('name')
            results += [agency.name for agency in agencies]
        json = simplejson.dumps(results)
        return HttpResponse(json, mimetype='application/json')
    elif request.method == 'POST':
        form = RequestForm(request.POST)
        # drop the data into SESSION_NAME
        if form.is_valid():
            title = form.title
            document = form.document
            if form.jurisdiction == 'f':
                jurisdiction = Jurisdiction.objects.filter(level='f')
            elif form.jurisdiction == 's':
                jurisdiction = form.state
            else:
                jurisdiction = form.locality
            agency = Agency.objects.filter(name=form.agency)
            is_new_agency = False
            if not agency:
                agency = form.agency
                is_new_agency = True
            request.session[SESSION_ID] = {
                'title': title,
                'document': document,
                'jurisdiction': jurisdiction,
                'agency': agency,
                'is_new_agency': is_new_agency,
                'is_clone': clone
            }
    else:
        if clone:
            form = RequestForm(initial=initial_data)
        else:
            form = RequestForm()
    
    def render_to_response(
        'forms/foia/create.html',
        {'form': form, 'clone': clone},
        context_instance=RequestContext(request)
    )
    
        
def submit_request(request):
        
    def _compose_comm(document, jurisdiction):
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
        
        prepend = [intro + ' I hereby request the following records:']
        append = [waiver,
                 ('In the event that fees cannot be waived, I would be '
                  'grateful if you would inform me of the total charges in '     
                  'advance of fulfilling my request. I would prefer the '
                  'request filled electronically, by e-mail attachment if ' 
                  'available or CD-ROM if not.'),
                  ('Thank you in advance for your anticipated cooperation in '
                  'this matter. I look forward to receiving your response to ' 
                  'this request within %s, as the statute requires.' % delay )]
        return prepend + [document] + append
        
    def _create_request(foia):
        title = foia['title']
        document = foia['document']
        slug = slugify(title) or 'untitled'
        jurisdiction = foia['jurisdiction']
        agency = foia['agency']
        is_new_agency = foia['is_new_agency']
        is_clone = foia['is_clone']
        if is_new_agency:
            agency = Agency.objects.create(
                name=new_agency[:255],
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
            communication=_compose_comm(document, jurisdiction)
        )
        foia_comm = foia.communications.all()[0]
        foia_comm.date = datetime.now()
        return foia, foia_comm, is_new_agency
    
    if request.session.get(SESSION_NAME, False):
        try:
            foia_request = pickle.loads(request.session[SESSION_NAME])
        except pickle.UnpicklingError as e:
            print e
            return redirect('index')
    else:
        return redirect('index')
    
    if request.method == 'POST':
        command = request.POST.get('submit', False)
        if command:
            if command == 'Submit' or command == 'Save Draft':
                foia, foia_comm, is_new_agency = _create_request(foia_request)
                if command == 'Submit':
                    foia.status = 'submitted'
                if request.user.get_profile().make_request():
                    # foia.submit() # DEBUG! Connection refused on local server
                    messages.success(request, 'Request succesfully submitted.')
                else:
                    foia.status = 'started'
                    error_msg = ('You are out of requests for this month. '
                                 'Your request has been saved as a draft.')
                    messages.error(request, error_msg)
                foia_comm.save()
                print 'comm saved' # DEBUG
                foia.save()
                print 'foia saved' # DEBUG

                del request.session[SESSION_NAME]

                if is_new_agency:
                    args = {
                        'jurisdiction': foia.agency.jurisdiction.slug,
                        'jidx': foia.agency.jurisdiction.pk,
                        'slug': foia.agency.slug,
                        'idx': foia.agency.pk
                    }
                    return redirect('agency-update', foia=foia.pk, kwargs=args)
                else:
                    return redirect(foia)
            else:    
                del request.session[SESSION_NAME]
                if command == 'Start Over':
                    return redirect('foia-create')
                return redirect('index')
    
    context = {
        'title': foia_request['title'],
        'agency': foia_request['agency'],
        'jurisdiction': foia_request['jurisdiction'],
        'comm': _compose_comm(
            foia_request['document'],
            foia_request['jurisdiction']
        ),
        'is_clone': foia_request['is_clone']
    }

    return render_to_response('forms/foia/confirm.html', context, 
                              context_instance=RequestContext(request))