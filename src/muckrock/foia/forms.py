"""
Forms for FOIA application
"""

from django import forms
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.defaultfilters import slugify
from django.template import RequestContext
from django.template.loader import render_to_string

import inspect
import sys
from datetime import datetime

from foia.models import FOIARequest, Jurisdiction, AgencyType
from foia.utils import make_template_choices
from foia.validate import validate_date_order
from formwizard.forms import DynamicSessionFormWizard
from widgets import CalendarWidget

class FOIARequestForm(forms.ModelForm):
    """A form for a FOIA Request"""

    embargo = forms.BooleanField(required=False,
                                 help_text='Putting an embargo on a request will hide it '
                                           'from others for 30 days after the response is received')
    agency_type = forms.ModelChoiceField(label='Agency', queryset=AgencyType.objects.all())

    class Meta:
        # pylint: disable-msg=R0903
        model = FOIARequest
        fields = ['title', 'jurisdiction', 'agency_type', 'embargo', 'request']
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

    clean = validate_date_order('date_begin', 'date_end')

    slug = 'mug_shot'
    name = 'Mug Shots'
    category = 'Crime'
    level = 'ls'
    agency = 'Police'

class FOIACriminalForm(FOIAWizardParent):
    """A form to fill in a criminal record template"""

    full_name = forms.CharField(help_text='Full name of person whose criminal record you want')
    birth_date = forms.DateField(required=False, label='Date of birth',
                                 help_text='If known',
                                 widget=CalendarWidget(attrs={'class': 'datepicker'}))

    slug = 'crime'
    name = 'Criminal Record'
    category = 'Crime'
    level = 's'
    agency = 'Police'

class FOIAAssessorForm(FOIAWizardParent):
    """A form to fill in an assessor template"""

    last_year = datetime.now().year - 1
    year = forms.IntegerField(min_value=1900, max_value=last_year, initial=last_year,
                              help_text='The year for which you want the data')

    slug = 'assesor'
    name = "Assesor's Data"
    category = 'Finance'
    level = 'l'
    agency = 'Clerk'

class FOIASalaryForm(FOIAWizardParent):
    """A form to fill in a salary template"""

    last_year = datetime.now().year - 1
    department = forms.CharField(help_text='Government department from which you '
                                           'want salary information')
    year = forms.IntegerField(min_value=1900, max_value=last_year, initial=last_year,
                              help_text='The year for which you want the data')

    slug = 'salary'
    name = 'Salaray Data'
    category = 'Finance'
    level = 'l'
    agency = 'Finance'

class FOIAContractForm(FOIAWizardParent):
    """A form to fill in a contract template"""

    department = forms.CharField(help_text='e.g. Schools, Fire, Parks & Recreations, etc.')
    companies = forms.CharField(
            label='Which company/companies',
            help_text='One per line',
            widget=forms.Textarea(attrs={'style': 'width:450px; height:80px'}))

    slug = 'contract'
    name = 'Contracts'
    category = 'Finance'
    level = 'ls'
    agency = 'Clerk'

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

    clean = validate_date_order('birth_date', 'death_date')

    slug = 'birth'
    name = 'Birth Record'
    category = 'Genealogy'
    level = 'l'
    agency = 'Health'

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

    clean = validate_date_order('birth_date', 'death_date')

    slug = 'death'
    name = 'Death Record'
    category = 'Genealogy'
    level = 'l'
    agency = 'Health'

class FOIAEmailForm(FOIAWizardParent):
    """A form to fill in an email request template"""

    full_name = forms.CharField(help_text='Government employee you would like the emails of')
    department = forms.CharField(help_text='Department or office he or she is in')
    date_begin = forms.DateField(help_text='Start of seven day period of emails',
                                 widget=CalendarWidget(attrs={'class': 'datepicker'}))

    slug = 'emails'
    name = 'Week of Email'
    category = 'Bureaucracy'
    level = 'lsf'
    agency = 'Clerk'

class FOIAExpenseForm(FOIAWizardParent):
    """A form to fill in an expense report request template"""

    full_name = forms.CharField(help_text='Government employee you would like the emails of')
    department = forms.CharField(help_text='Department or office he or she is in')
    months_back = forms.IntegerField(help_text='How many months back')

    slug = 'expense'
    name = 'Expense Reports'
    category = 'Finance'
    level = 'lsf'
    agency = 'Finance'

class FOIAMinutesForm(FOIAWizardParent):
    """A form to fill in a meeting minutes request template"""

    group = forms.CharField(help_text='Government group, board, or panel you want the minutes from')
    meetings_back = forms.IntegerField(help_text='How many meetings back')

    slug = 'minutes'
    name = 'Meeting Minutes'
    category = 'Bureaucracy'
    level = 'lsf'
    agency = 'Clerk'

class FOIATravelForm(FOIAWizardParent):
    """A form to fill in a travel expense request template"""

    full_name = forms.CharField(help_text='Government employee you would like travel recipets from')
    department = forms.CharField(help_text='Department or office he or she is in')

    slug = 'travel'
    name = 'Travel Expense Reports'
    category = 'Finance'
    level = 'lsf'
    agency = 'Finance'

class FOIAAthleticForm(FOIAWizardParent):
    """A form to fill in an athletic personal salary request template"""

    school = forms.CharField(help_text='School you would like the athletic personnel salaries for')

    slug = 'athletic'
    name = 'Athletic Personel Salaries'
    category = 'Finance'
    level = 'ls'
    agency = 'Finance'

class FOIAPetForm(FOIAWizardParent):
    """A form to fill in a pet license request template"""
    
    slug = 'pets'
    name = 'Pet Licensing Data'
    category = 'Health'
    level = 'l'
    agency = 'Health'

class FOIAParkingForm(FOIAWizardParent):
    """A form to fill in a waived parking ticket template"""

    date_begin = forms.DateField(widget=CalendarWidget(attrs={'class': 'datepicker'}))
    date_end = forms.DateField(widget=CalendarWidget(attrs={'class': 'datepicker'}))

    clean = validate_date_order('date_begin', 'date_end')

    slug = 'parking'
    name = 'Parking Ticket Waivers'
    category = 'Crime'
    level = 'l'
    agency = 'Police'

class FOIRestaurantForm(FOIAWizardParent):
    """A form to fill in a restaurant health inspeaction template"""

    restaurant = forms.CharField()
    address = forms.CharField(help_text='Full address of the restaurant',
                              widget=forms.Textarea(attrs={'style': 'width:450px; height:32px'}))
    past_records = forms.BooleanField(required=False, help_text='Check to obtain past records')
    year = forms.IntegerField(required=False, help_text='Year you want past records back to')

    slug = 'restaurant'
    name = 'Restaurant Health Inspection'
    category = 'Health'
    level = 'l'
    agency = 'Health'

    def clean(self):
        """Year is required only is past_records is checked"""

        past_records = self.cleaned_data.get('past_records')
        year = self.cleaned_data.get('year')

        if past_records and year is None:
            self._errors['year'] = self.error_class(
                    ['Year is required if you would like to obtain past records'])

        return self.cleaned_data

class FOIASexOffenderForm(FOIAWizardParent):
    """A form to fill in a sex offender template"""
    # how should blank ones work???

    slug = 'sex'
    name = 'Sex Offender Registry'
    category = 'Crime'
    level = 'l'
    agency = 'Police'

class FOIABlankForm(FOIAWizardParent):
    """A form with no specific template"""

    title = forms.CharField(help_text='Be concise and descriptive', max_length=70,
                            widget=forms.TextInput(attrs={'style': 'width:450px'}))
    document_request = forms.CharField(
            help_text='One sentence describing the specific document you want',
            widget=forms.Textarea(attrs={'style': 'width:450px; height:32px'}))

    slug = 'none'
    name = 'None'
    category = None
    level = 'lsf'
    agency = 'Clerk'

TEMPLATES = dict((form.slug, form) for form_name, form in inspect.getmembers(sys.modules[__name__],
                 lambda member: inspect.isclass(member) and issubclass(member, FOIAWizardParent))
                 if form is not FOIAWizardParent)
LOCAL_TEMPLATE_CHOICES   = make_template_choices(TEMPLATES, 'l')
STATE_TEMPLATE_CHOICES   = make_template_choices(TEMPLATES, 's')
FEDERAL_TEMPLATE_CHOICES = make_template_choices(TEMPLATES, 'f')

class FOIAWizardWhereForm(forms.Form):
    """A form to select the jurisdiction to file the request in"""

    level = forms.ChoiceField(choices=(('federal', 'Federal'),
                                       ('state', 'State'),
                                       ('local', 'Local')))
    state = forms.ModelChoiceField(queryset=Jurisdiction.objects.filter(level='s'), required=False)
    local = forms.ModelChoiceField(queryset=Jurisdiction.objects.filter(level='l'), required=False)

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

class FOIAWhatFederalForm(forms.Form):
    """A form to select what template to use for a federal request"""

    template = forms.ChoiceField(choices=FEDERAL_TEMPLATE_CHOICES)

class FOIAWizard(DynamicSessionFormWizard):
    """Wizard to create FOIA requests"""
    # pylint: disable-msg=R0904

    def done(self, request, form_list):
        """Wizard has been completed"""

        template = form_list[1].cleaned_data['template']

        level = form_list[0].cleaned_data['level']
        if level == 'local' or level == 'state':
            jurisdiction = form_list[0].cleaned_data[level]
        elif level == 'federal':
            jurisdiction = Jurisdiction.objects.get(level='f')
        else: # pragma: no cover
            return render_to_response('error.html',
                     {'message': 'There was an error during form processing'},
                     context_instance=RequestContext(request))

        template_file = 'request_templates/%s.txt' % template
        data = form_list[2].cleaned_data
        data['jurisdiction'] = jurisdiction.name

        title, foia_request = \
            (s.strip() for s in render_to_string(template_file, data,
                                                 RequestContext(request)).split('\n', 1))
        agency_type = TEMPLATES[template].agency

        if len(title) > 70:
            title = title[:70]
        foia = FOIARequest.objects.create(user=request.user, status='started',
                                          jurisdiction=jurisdiction, title=title,
                                          request=foia_request, slug=slugify(title),
                                          agency_type=AgencyType.objects.get(name=agency_type))

        messages.success(request, 'Request succesfully created.  Please review it and make any '
                                  'changes that you need.  You may save it for future review or '
                                  'submit it when you are ready.')

        return HttpResponseRedirect(reverse('foia-update',
                                    kwargs={'jurisdiction': jurisdiction.slug,
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
            elif level == 'federal':
                self.append_form_list('FOIAWhatFederalForm', 1)
                self.update_extra_context({'template_choices': FEDERAL_TEMPLATE_CHOICES})

        # add final template specific step
        if self.get_step_index() == 1:
            template = TEMPLATES[form.cleaned_data['template']]
            self.update_extra_context({'heading': template.name})
            self.append_form_list(template.__name__, 2)

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


