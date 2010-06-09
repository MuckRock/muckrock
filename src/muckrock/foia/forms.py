"""
Forms for FOIA application
"""

from django import forms
from django.template.defaultfilters import slugify
from django.forms.util import ErrorList
from django.http import HttpResponseRedirect
from django.contrib.formtools.wizard import FormWizard
from django.template.loader import render_to_string
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.contrib import messages

from datetime import datetime
from collections import namedtuple

from foia.models import FOIARequest, STATE_JURISDICTIONS, LOCAL_JURISDICTIONS
from foia.utils import make_template_choices, get_jurisdiction_display
from widgets import CalendarWidget

class FOIARequestForm(forms.ModelForm):
    """A form for a FOIA Request"""

    def clean(self):
        """Check user and slug are unique together"""

        forms.ModelForm.clean(self)

        # if no title, just return, let field error be raised
        if 'title' not in self.cleaned_data:
            return self.cleaned_data

        user = self.instance.user
        slug = slugify(self.cleaned_data['title'])

        other_foias = FOIARequest.objects.filter(user=user, slug=slug)

        if len(other_foias) == 1 and other_foias[0] != self.instance:
            self._errors['title'] = \
                ErrorList(['You already have a FOIA request with a similar title'])

        if len(other_foias) > 1: # pragma: no cover
            # this should never happen
            self._errors['title'] = \
                ErrorList(['You already have a FOIA request with a similar title'])

        return self.cleaned_data

    class Meta:
        # pylint: disable-msg=R0903
        model = FOIARequest
        fields = ['title', 'jurisdiction', 'agency', 'request']
        widgets = {
                'title': forms.TextInput(attrs={'style': 'width:450px;'}),
                'request': forms.Textarea(attrs={'style': 'width:450px; height: 200px;'}),
                }


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


class FOIAWizard(FormWizard):
    """Wizard to create FOIA requests"""

    def __init__(self, *args, **kwargs):
        FormWizard.__init__(self, *args, **kwargs)
        self.extra_context = {
                'state_list': STATE_JURISDICTIONS,
                'local_list': LOCAL_JURISDICTIONS,
                }

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
        FOIARequest.objects.create(user=request.user, status='started',
                                   jurisdiction=jurisdiction, title=title,
                                   request=foia_request, slug=slugify(title),
                                   agency=agency)

        messages.success(request, 'Request succesfully created.  Please review it and make any '
                                  'changes that you need.  You may save it for future review or '
                                  'submit it when you are ready.')

        return HttpResponseRedirect(reverse('foia-update',
                                    kwargs={'jurisdiction': jurisdiction,
                                            'user_name': request.user.username,
                                            'slug': slugify(title)}))

    def process_step(self, request, form, step):
        """Process each step"""

        # add 'what' step
        if self.determine_step(request) == 0 and step == 0:
            level = form.cleaned_data['level']
            if level == 'local':
                new_form = FOIAWhatLocalForm
                self.extra_context.update({'template_choices': LOCAL_TEMPLATE_CHOICES})
            elif level == 'state':
                new_form = FOIAWhatStateForm
                self.extra_context.update({'template_choices': STATE_TEMPLATE_CHOICES})

            if len(self.form_list) == 1:
                self.form_list.append(new_form)
            elif len(self.form_list) > 1:
                # state may be saved if they start over without finishing
                self.form_list[1] = new_form

        # total number of steps - add on the last form
        num_steps = 3
        if self.determine_step(request) == num_steps - 2 and step == num_steps - 2:
            template = TEMPLATES[form.cleaned_data['template']]
            self.extra_context.update({'heading': template.name})
            if len(self.form_list) == num_steps - 1:
                self.form_list.append(template.form)
            elif len(self.form_list) == num_steps:
                # state may be saved if they start over without finishing
                self.form_list[num_steps - 1] = template.form
            elif len(self.form_list) > num_steps:
                # error, this should never happen
                pass

    def get_template(self, step):
        """Template name"""

        if step == 0:
            return 'foia/foiawizard_where.html'
        elif step == 1:
            return 'foia/foiawizard_what.html'
        else:
            return 'foia/foiawizard_form.html'

