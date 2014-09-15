from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.formtools.wizard.views import SessionWizardView
from django.http import HttpResponseRedirect
from django.template.loader import render_to_string, get_template
from django.template import RequestContext

import muckrock.foia.new_forms as forms

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
        
    def get_form_initial(self, step):
        initial = self.initial_dict.get(step, {})
        if step == 2:
            j = self.get_cleaned_data_for_step('0')['jurisdictions']
            initial.update({'j': j})
        return initial

    def done(self, form_list, **kwargs):
        data = self.get_all_cleaned_data()
        agencies = data['agencies']
        multi = len(agencies) > 1
        _process_multi(form_list) if multi else _process_single(form_list)
        return HttpResponseRedirect('index')