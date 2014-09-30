from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.formtools.wizard.views import SessionWizardView
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, redirect
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string, get_template
from django.template import RequestContext

from muckrock.agency.models import Agency
import muckrock.foia.new_forms as forms
from muckrock.foia.models import FOIARequest, FOIACommunication
from muckrock.jurisdiction.models import Jurisdiction

import pickle
from datetime import datetime
import logging
logger = logging.getLogger(__name__)

FORMS = [
    ('document', forms.DocumentForm),
    ('jurisdiction', forms.JurisdictionForm),
    ('agency', forms.AgencyForm)
]

TEMPLATES = {
    'document': 'foia/create/document.html',
    'jurisdiction': 'foia/create/jurisdiction.html',
    'agency': 'foia/create/agency.html',
    'fallback': 'foia/create/base_create.html'
}

SESSION_NAME = 'foia_request'

class RequestWizard(SessionWizardView):
    
    jurisdiction = [] 
    
    def _get_jurisdiction_list(self):
        """Creates a list of all chosen jurisdictions"""
        j_list = []
        data = self.get_cleaned_data_for_step('jurisdiction')
        is_state, is_local = data['is_state'], data['is_local']
        state, local = data['state'], data['local']
        if data.get('is_federal'):
            j_list += Jurisdiction.objects.filter(level='f', hidden=False)
        if is_state:
            the_state = Jurisdiction.objects.filter(level='s', abbrev=state)
            j_list += the_state
            if is_local and not local:
                s_id = the_state[0].id
                j_list += Jurisdiction.objects.filter(level='l', parent=s_id)
        if is_local:
            j_list += Jurisdiction.objects.filter(level='l', full_name=local)
        args = {'jurisdictions': j_list}
        self.jurisdiction = j_list
        return args
    
    def _save_summary(self):
        doc_input = self.get_cleaned_data_for_step('document')
        agency_input = self.get_cleaned_data_for_step('agency')
        user = self.request.user if not self.request.user.is_anonymous() \
                                 else False
        title = doc_input['title']
        document = doc_input['document']
        new_agencies = agency_input['other'].split(',')
        for i, j in enumerate(new_agencies):
            new_agencies[i] = j.lstrip()
            if not new_agencies[i]: # cleans out empty strings from array
                new_agencies.remove(new_agencies[i])
        agencies = [key for key, value in agency_input.items() if key != 'other' and value != False]
        for i, agency in enumerate(agencies):
            agencies[i] = (Agency.objects.filter(name=agency))[0]
            # the .filter() function returns a QuerySet,
            # so the first element of that set is taken as the agency
        args = {
            'title': title,
            'document': document,
            'jurisdiction': self.jurisdiction,
            'agencies': agencies,
            'new_agencies': new_agencies
        }
        self.request.session[SESSION_NAME] = pickle.dumps(args)
        
    def get_form_initial(self, step):
        initial = self.initial_dict.get(step, {})
        args = {}
        if step == 'agency':
            args = self._get_jurisdiction_list()
        initial.update(args)
        return initial
    
    def get_template_names(self):
        return [TEMPLATES[self.steps.current], TEMPLATES['fallback']]
    
    def done(self, form_list, **kwargs):
        try:
            self._save_summary()
        except pickle.PicklingError as e:
            print e
        return redirect('foia-submit')
        
def submit_request(request):
        
    def _compose_preview(document, agencies):
        intro = 'This is a request under the Freedom of Information Act.'
        waiver = ('I also request that, if appropriate, fees be waived as I '
                  'believe this request is in the public interest. '
                  'The requested documents  will be made available to the ' 
                  'general public free of charge as part of the public ' 
                  'information service at MuckRock.com, processed by a ' 
                  'representative of the news media/press and is made in the ' 
                  ' process of news gathering and not for commercial usage.')
        delay = '20 business days'
        
        if len(agencies) == 1:
            j = agencies[0].jurisdiction
            if j.get_intro():
                intro = j.get_intro()                
            if j.get_waiver():
                waiver = j.get_waiver()
            if j.get_days():
                delay = j.get_days()
        
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
        slug = slugify(foia['title']) or 'untitled'
        jurisdiction = foia['jurisdiction'][0]
        if foia['agencies']:
            agency = foia['agencies'][0]
            is_new_agency = False
        else:
            new_agency = foia['new_agencies'][0]
            agency = Agency.objects.create(
                name=new_agency[:255],
                slug=(slugify(new_agency[:255]) or 'untitled'),
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
        foia = FOIARequest.objects.create(
            user=request.user,
            status='started',
            title=foia['title'],
            jurisdiction=jurisdiction,
            slug=slug,
            agency=agency,
            requested_docs=foia['document'],
            description=foia['document']
        )
        FOIACommunication.objects.create(
            foia=foia,
            from_who=request.user.get_full_name(),             
            to_who=foia.get_to_who(),
            date=datetime.now(),
            response=False,
            full_html=False,
            communication=request_text
        )
        foia_comm = foia.communications.all()[0]
        foia_comm.date = datetime.now()
        return foia, foia_comm, is_new_agency
    
    if request.session.get(SESSION_NAME, False):
        try:
            foia_request = pickle.loads(request.session[SESSION_NAME])
        except pickle.UnpicklingError as e:
            print e
    else:
        return redirect('index')
        
    agency_names = [agency.name for agency in foia_request['agencies']] + \
                    foia_request['new_agencies']
    request_text = _compose_preview(foia_request['document'],
                                    foia_request['agencies'])
    
    if request.method == 'POST':
        command = request.POST.get('submit', False)
        if command:
            if command == 'Submit' or command == 'Save Draft':
                foia, foia_comm, new_agency = _create_request(foia_request)
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

                if new_agency:
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
        'agency_names': agency_names,
        'request_text': request_text
    }

    return render_to_response('foia/create/confirm.html', context, 
                              context_instance=RequestContext(request))