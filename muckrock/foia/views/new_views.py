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



class RequestWizard(SessionWizardView):
    template_name = 'foia/new.html'

    def _process_single(self, form_list):
        user = self.request.user
        profile = user.get_profile()
        return None
    
    def _process_multi(self, form_list):
        user = self.request.user
        profile = user.get_profile()
        return None
        
    def get_jurisdiction_list(self):
        """Creates a list of all chosen jurisdictions"""
        j_list = []
        data = self.get_cleaned_data_for_step('jurisdiction')
        is_state, is_local = data['is_state'], data['is_local']
        state, local = data['state'], data['local']
        if data.get('is_federal'):
            j_list += Jurisdiction.objects.filter(level='f', hidden=False)
        if is_state:
            j_list += Jurisdiction.objects.filter(level='s', abbrev=state)
            if is_local and not local:
                j_list += Jurisdiction.objects.filter(level='l', parent=j.id)
        if is_local:
            j_list += Jurisdiction.objects.filter(level='l', full_name=local)
        return j_list
        
    def get_form_initial(self, step):
        initial = self.initial_dict.get(step, {})
        if step == 'agency':
            jurisdictions = self.get_jurisdiction_list()
            initial.update({'jurisdictions': jurisdictions})
        elif step == 'confirm':
            request_input = self.get_cleaned_data_for_step('request')
            agency_input = self.get_cleaned_data_for_step('agency')
            title = request_input['title']
            request = request_input['request']
            agencies = []
            for agency_choice in agency_input:
                agency = [agency_choice] if agency_input[agency_choice] else []
                agencies += agency
            args = {'title': title, 'request': request, 'agencies': agencies}
            initial.update(args)
        return initial

    def done(self, form_list, **kwargs):
        data = self.get_all_cleaned_data()
        agencies = data['agencies']
        multi = len(agencies) > 1
        _process_multi(form_list) if multi else _process_single(form_list)
        return HttpResponseRedirect('index')