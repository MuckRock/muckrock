from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.formtools.wizard.views import SessionWizardView
from django.http import HttpResponseRedirect
from django.template.loader import render_to_string, get_template
from django.template import RequestContext

import muckrock.foia.new_forms as forms
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.agency.models import Agency

import logging
logger = logging.getLogger(__name__)

FORMS = [
    ('document', forms.DocumentForm),
    ('jurisdiction', forms.JurisdictionForm),
    ('agency', forms.AgencyForm),
    ('confirm', forms.ConfirmationForm)
]

TEMPLATES = {
    'document': 'foia/create/document.html',
    'jurisdiction': 'foia/create/jurisdiction.html',
    'agency': 'foia/create/agency.html',
    'confirm': 'foia/create/confirm.html',
    'fallback': 'foia/create/base_create.html'
}

class RequestWizard(SessionWizardView):

    agency_list = []
    new_agency_list = []

    def _process_single(self, form_list):
        user = self.request.user
        profile = user.get_profile()
        return None
    
    def _process_multi(self, form_list):
        user = self.request.user
        profile = user.get_profile()
        return None
        
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
        return args
    
    def _get_summary(self):
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
            'user': user,
            'title': title,
            'document': document,
            'agencies': agencies,
            'new_agencies': new_agencies
        }
        self.new_agency_list = new_agencies
        self.agency_list = agencies
        
        return args
        
    def get_form_initial(self, step):
        initial = self.initial_dict.get(step, {})
        args = {}
        if step == 'agency':
            args = self._get_jurisdiction_list()
        elif step == 'confirm':
            args = self._get_summary()
            print args
        initial.update(args)
        return initial
    
    def get_template_names(self):
        return [TEMPLATES[self.steps.current], TEMPLATES['fallback']]
    
    def done(self, form_list, **kwargs):
        data = self.get_all_cleaned_data()
        multi = len(self.agency_list + self.new_agency_list) > 1
        _process_multi(form_list) if multi else _process_single(form_list)
        return HttpResponseRedirect('index')