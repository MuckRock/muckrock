from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.formtools.wizard.views import SessionWizardView
from django.http import HttpResponseRedirect
from django.template.loader import render_to_string, get_template
from django.template import RequestContext

import muckrock.foia.new_forms as forms
from muckrock.jurisdiction.models import Jurisdiction

import logging
logger = logging.getLogger(__name__)

FORMS = [
    ('request', forms.RequestForm),
    ('jurisdiction', forms.JurisdictionForm),
    ('agency', forms.AgencyForm),
    ('confirm', forms.ConfirmationForm)
]

TEMPLATES = {
    'request': 'foia/create/request.html',
    'jurisdiction': 'foia/create/jurisdiction.html',
    'agency': 'foia/create/agency.html',
    'confirm': 'foia/create/confirm.html',
    'fallback': 'foia/create/base_create.html'
}

class RequestWizard(SessionWizardView):

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
        user = self.request.user
        request_input = self.get_cleaned_data_for_step('request')
        agency_input = self.get_cleaned_data_for_step('agency')
        title = request_input['title']
        document = request_input['document']
        agencies = []
        for agency_choice in agency_input:
            agency = [agency_choice] if agency_input[agency_choice] else []
            agencies += agency
        new_agency = agency_input['other']
        args = {
            'user': user,
            'title': title,
            'document': document,
            'agencies': agencies,
            'new_agency': new_agency
        }
        return args
        
    def get_form_initial(self, step):
        initial = self.initial_dict.get(step, {})
        args = {}
        if step == 'agency':
            args = self._get_jurisdiction_list()
        if step == 'confirm':
            args = self._get_summary()   
        initial.update(args)
        return initial
    
    def get_template_names(self):
        return [TEMPLATES[self.steps.current], TEMPLATES['fallback']]

    def done(self, form_list, **kwargs):
        data = self.get_all_cleaned_data()
        agencies = data['agencies']
        multi = len(agencies) > 1
        _process_multi(form_list) if multi else _process_single(form_list)
        return HttpResponseRedirect('index')