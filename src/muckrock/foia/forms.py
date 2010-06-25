"""
Forms for FOIA application
"""

from django import forms
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.template.defaultfilters import slugify
from django.template import RequestContext
from django.template.loader import render_to_string

from collections import namedtuple
from datetime import datetime

from foia.models import FOIARequest, STATE_JURISDICTIONS, LOCAL_JURISDICTIONS
from foia.utils import make_template_choices, get_jurisdiction_display
from formwizard.forms import DynamicSessionFormWizard
from widgets import CalendarWidget

class FOIARequestForm(forms.ModelForm):
    """A form for a FOIA Request"""

    class Meta:
        # pylint: disable-msg=R0903
        model = FOIARequest
        fields = ['title', 'jurisdiction', 'agency', 'request']
        widgets = {
                'title': forms.TextInput(attrs={'style': 'width:450px;'}),
                'request': forms.Textarea(attrs={'style': 'width:450px; height: 200px;'}),
                }


class FOIADeleteForm(forms.Form):
    """Form to confirm deleting a FOIA Request"""

    confirm = forms.BooleanField(label='Are you sure you want to delete this FOIA request?',
                                 help_text='This cannot be undone!')


class FOIAWizardParent(forms.Form):
    """A form with generic options for every template"""

    max_pay = forms.IntegerField(label='What will you pay for the request?',
                                 help_text="We'll cover the first $5",
                                 min_value=5, initial=5,
                                 widget=forms.TextInput(attrs={'size': 2}))


class FOIAMugShotForm(FOIAWizardParent):
    """A form to fill in a mug shot template"""

    full_name = forms.CharField(help_text='Full name of person whose mug shots you want')
    date_begin = forms.DateField(help_text='Range of dates in which the mug shots were taken',
                                 widget=CalendarWidget(attrs={'class': 'datepicker'}))
    date_end = forms.DateField(widget=CalendarWidget(attrs={'class': 'datepicker'}))


class FOIACriminalForm(FOIAWizardParent):
    """A form to fill in a criminal record template"""

    full_name = forms.CharField(help_text='Full name of person whose criminal record you want')
    birth_date = forms.DateField(required=False, label='Date of birth',
                                 help_text='If known',
                                 widget=CalendarWidget(attrs={'class': 'datepicker'}))


class FOIAAssessorForm(FOIAWizardParent):
    """A form to fill in an assessor template"""

    last_year = datetime.now().year - 1
    year = forms.IntegerField(min_value=1900, max_value=last_year, initial=last_year,
                              help_text='The year for which you want the data')


class FOIASalaryForm(FOIAWizardParent):
    """A form to fill in a salary template"""

    last_year = datetime.now().year - 1
    department = forms.CharField(help_text='Government department from which you '
                                           'want salary information')
    year = forms.IntegerField(min_value=1900, max_value=last_year, initial=last_year,
                              help_text='The year for which you want the data')


class FOIAContractForm(FOIAWizardParent):
    """A form to fill in a contract template"""

    department = forms.CharField(help_text='e.g. Schools, Fire, Parks & Recreations, etc.')
    companies = forms.CharField(
            label='Which company/companies',
            help_text='One per line',
            widget=forms.Textarea(attrs={'style': 'width:450px; height:80px'}))


class FOIABirthForm(FOIAWizardParent):
    """A form to fill in a birth certificate template"""

    full_name = forms.CharField(help_text='Full name of person whose birth record you want')
    birth_date = forms.DateField(label='Date of birth',
                                 widget=CalendarWidget(attrs={'class': 'datepicker'}))
    death_date = forms.DateField(label='Date of death',
                                 help_text='In many states, only individuals deceased for over 75 '
                                           'years have their records available for geneological '
                                           'inspection',
                                 widget=CalendarWidget(attrs={'class': 'datepicker'}))
    interest = forms.CharField(
            required=False,
            help_text='A brief sentence about your geneological interest in this individual',
            widget=forms.Textarea(attrs={'style': 'width:450px; height:32px'}))


class FOIADeathForm(FOIAWizardParent):
    """A form to fill in a death certificate template"""

    full_name = forms.CharField(help_text='Full name of person whose death record you want')
    birth_date = forms.DateField(label='Date of birth',
                                 widget=CalendarWidget(attrs={'class': 'datepicker'}))
    death_date = forms.DateField(label='Date of death',
                                 help_text='In many states, only individuals deceased for over 75 '
                                           'years have their records available for geneological '
                                           'inspection',
                                 widget=CalendarWidget(attrs={'class': 'datepicker'}))
    interest = forms.CharField(
            required=False,
            help_text='A brief sentence about your geneological interest in this individual',
            widget=forms.Textarea(attrs={'style': 'width:450px; height:32px'}))


class FOIABlankForm(FOIAWizardParent):
    """A form with no specific template"""

    title = forms.CharField(help_text='Be concise and descriptive', max_length=70,
                            widget=forms.TextInput(attrs={'style': 'width:450px'}))
    document_request = forms.CharField(
            help_text='One sentence describing the specific document you want',
            widget=forms.Textarea(attrs={'style': 'width:450px; height:32px'}))


Template = namedtuple('Template', 'id, name, category, level, form')
TEMPLATES = {
    'mug_shot': Template('mug_shot', 'Mug Shots',       'Crime',     'both',  FOIAMugShotForm),
    'crime':    Template('crime',    'Criminal Record', 'Crime',     'state', FOIACriminalForm),
    'assessor': Template('assessor', "Assessor's Data", 'Finances',  'local', FOIAAssessorForm),
    'salary':   Template('salary',   'Salary Data',     'Finances',  'local', FOIASalaryForm),
    'contract': Template('contract', 'Contracts',       'Finances',  'both',  FOIAContractForm),
    'birth':    Template('birth',    'Birth Record',    'Genealogy', 'local', FOIABirthForm),
    'death':    Template('death',    'Death Record',    'Genealogy', 'local', FOIADeathForm),
    'none':     Template('none',     'None',            None,        'both',  FOIABlankForm),
    }

LOCAL_TEMPLATE_CHOICES = make_template_choices(TEMPLATES, 'local')
STATE_TEMPLATE_CHOICES = make_template_choices(TEMPLATES, 'state')


class FOIAWizardWhereForm(forms.Form):
    """A form to select the jurisdiction to file the request in"""

    level = forms.ChoiceField(choices=(('national', 'National'),
                                       ('state', 'State'),
                                       ('local', 'Local')))
    state = forms.ChoiceField(choices=STATE_JURISDICTIONS, required=False)
    local = forms.ChoiceField(choices=LOCAL_JURISDICTIONS, required=False)

    def clean(self):
        """Make sure state or local is required based off of choice of level"""

        level = self.cleaned_data.get('level')
        state = self.cleaned_data.get('state')
        local = self.cleaned_data.get('local')

        if level == 'state' and not state:
            self._errors['state'] = self.error_class(
                    ['State required if you choose to file at the state level'])

        if level == 'local' and not local:
            self._errors['local'] = self.error_class(
                    ['Local required if you choose to file at the local level'])

        return self.cleaned_data


class FOIAWhatLocalForm(forms.Form):
    """A form to select what template to use for a local request"""

    template = forms.ChoiceField(choices=LOCAL_TEMPLATE_CHOICES)


class FOIAWhatStateForm(forms.Form):
    """A form to select what template to use for a state request"""

    template = forms.ChoiceField(choices=STATE_TEMPLATE_CHOICES)


class FOIAWizard(DynamicSessionFormWizard):
    """Wizard to create FOIA requests"""
    # pylint: disable-msg=R0904

    def done(self, request, form_list):
        """Wizard has been completed"""

        template = form_list[1].cleaned_data['template']

        level = form_list[0].cleaned_data['level']
        if level == 'state':
            jurisdiction = form_list[0].cleaned_data['state']
        elif level == 'local':
            jurisdiction = form_list[0].cleaned_data['local']
        else:
            # shouldn't happen
            jurisdiction = ''

        template_file = 'request_templates/%s.txt' % template
        data = form_list[2].cleaned_data
        data.update({'jurisdiction': get_jurisdiction_display(jurisdiction)})

        title, agency, foia_request = \
            (s.strip() for s in render_to_string(template_file, data,
                                                 RequestContext(request)).split('\n', 2))
        assert title
        if len(title) > 70:
            title = title[:70]
        foia = FOIARequest.objects.create(user=request.user, status='started',
                                          jurisdiction=jurisdiction, title=title,
                                          request=foia_request, slug=slugify(title),
                                          agency=agency)

        messages.success(request, 'Request succesfully created.  Please review it and make any '
                                  'changes that you need.  You may save it for future review or '
                                  'submit it when you are ready.')

        return HttpResponseRedirect(reverse('foia-update',
                                    kwargs={'jurisdiction': jurisdiction,
                                            'idx': foia.id,
                                            'slug': slugify(title)}))

    def process_step(self, form):
        """Process each step"""

        # add 'what' step
        if self.get_step_index() == 0:
            level = form.cleaned_data['level']
            if level == 'local':
                self.append_form_list('FOIAWhatLocalForm', 1)
                self.update_extra_context({'template_choices': LOCAL_TEMPLATE_CHOICES})
            elif level == 'state':
                self.append_form_list('FOIAWhatStateForm', 1)
                self.update_extra_context({'template_choices': STATE_TEMPLATE_CHOICES})

        # add final template specific step
        if self.get_step_index() == 1:
            template = TEMPLATES[form.cleaned_data['template']]
            self.update_extra_context({'heading': template.name})
            self.append_form_list(template.form.__name__, 2)

        return self.get_form_step_data(form)

    def get_template(self):
        """Template name"""

        step = self.get_step_index()
        if step == 0:
            return 'foia/foiawizard_where.html'
        elif step == 1:
            return 'foia/foiawizard_what.html'
        else:
            return 'foia/foiawizard_form.html'


form_dict = dict((t.form.__name__, t.form) for t in TEMPLATES.values())
form_dict.update((form.__name__, form) for form in
                 [FOIAWizardWhereForm, FOIAWhatLocalForm, FOIAWhatStateForm])
foia_wizard = FOIAWizard(['FOIAWizardWhereForm'], form_dict)
wizard_extra_context = {'state_list': STATE_JURISDICTIONS, 'local_list': LOCAL_JURISDICTIONS}
