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

from foia.models import FOIARequest, FOIACommunication, FOIANote, Jurisdiction, Agency, AgencyType
from foia.utils import make_template_choices
from foia.validate import validate_date_order
from formwizard.forms import DynamicSessionFormWizard

class FOIARequestForm(forms.ModelForm):
    """A form for a FOIA Request"""

    embargo = forms.BooleanField(required=False,
                                 help_text='Embargoing a request keeps it completely private from '
                                           'other users until 30 days after you receive the final '
                                           'response to your request.')
    agency = forms.ModelChoiceField(label='Agency', required=False, queryset=Agency.objects.all(),
                                    widget=forms.Select(attrs={'class': 'agency-combo'}),
                                    help_text='Select one of the agencies for the jurisdiction you '
                                          'have chosen, or write in the correct agency if known')
    request = forms.CharField(widget=forms.Textarea(attrs={'style': 'width:450px; height:200px;'}))

    class Meta:
        # pylint: disable-msg=R0903
        model = FOIARequest
        fields = ['title', 'agency', 'embargo']
        widgets = {
                'title': forms.TextInput(attrs={'style': 'width:450px;'}),
                }

class FOIARequestTrackerForm(forms.ModelForm):
    """A form for a FOIA Request that is only tracked"""

    agency = forms.ModelChoiceField(label='Agency', required=False, queryset=Agency.objects.all(),
                                    widget=forms.Select(attrs={'class': 'agency-combo'}))

    class Meta:
        # pylint: disable-msg=R0903
        model = FOIARequest
        fields = ['title', 'status', 'jurisdiction', 'agency', 'date_submitted', 'date_due',
                  'date_done']
        widgets = {
                'title': forms.TextInput(attrs={'style': 'width:400px;'}),
                'date_submitted': forms.TextInput(attrs={'class': 'datepicker'}),
                'date_due': forms.TextInput(attrs={'class': 'datepicker'}),
                'date_done': forms.TextInput(attrs={'class': 'datepicker'}),
                }

class FOIADeleteForm(forms.Form):
    """Form to confirm deleting a FOIA Request"""

    confirm = forms.BooleanField(label='Are you sure you want to delete this FOIA request?',
                                 help_text='This cannot be undone!')

class FOIAFixForm(forms.Form):
    """Form to ammend a request with extra information"""
    fix = forms.CharField(widget=forms.Textarea(attrs={'style': 'width:450px; height:200px;'}))

class FOIANoteForm(forms.ModelForm):
    """A form for a FOIA Note"""

    class Meta:
        # pylint: disable-msg=R0903
        model = FOIANote
        fields = ['note']
        widgets = {'note': forms.Textarea(attrs={'style': 'width:450px; height:200px;'})}


class FOIAWizardParent(forms.Form):
    """A form with generic options for every template"""
    agency = None
    agency_type = None

    @classmethod
    def get_agency(cls, jurisdiction):
        """Get the agency for this template given a jurisdiction"""

        def get_first(list_):
            """Get first element of a list or none if it is empty"""
            if list_:
                return list_[0]

        agency = None
        if cls.agency:
            agency = get_first(Agency.objects.filter(name=cls.agency, jurisdiction=jurisdiction))
        if not agency and cls.agency_type:
            agency = get_first(Agency.objects.filter(
                types=get_first(AgencyType.objects.filter(name=cls.agency_type)),
                jurisdiction=jurisdiction))

        return agency

class FOIAMugShotForm(FOIAWizardParent):
    """A form to fill in a mug shot template"""

    full_name = forms.CharField(help_text='Full name of person whose mug shots you want')
    date_begin = forms.DateField(help_text='Range of dates in which the mug shots were taken',
                                 widget=forms.TextInput(attrs={'class': 'datepicker'}))
    date_end = forms.DateField(widget=forms.TextInput(attrs={'class': 'datepicker'}))

    clean = validate_date_order('date_begin', 'date_end')

    slug = 'mug_shot'
    name = 'Mug Shots'
    category = 'Crime'
    level = 'ls'
    agency_type = 'Police'
    short_desc = "Get somebody's mug shots."

class FOIACriminalForm(FOIAWizardParent):
    """A form to fill in a criminal record template"""

    full_name = forms.CharField(help_text='Full name of person whose criminal record you want')
    birth_date = forms.DateField(required=False, label='Date of birth',
                                 help_text='If known',
                                 widget=forms.TextInput(attrs={'class': 'datepicker'}))

    slug = 'crime'
    name = 'Criminal Record'
    category = 'Crime'
    level = 's'
    agency_type = 'Police'
    short_desc = 'Get the criminal record for an individual.'

class FOIAAssessorForm(FOIAWizardParent):
    """A form to fill in an assessor template"""

    last_year = datetime.now().year - 1
    year = forms.IntegerField(min_value=1900, max_value=last_year, initial=last_year,
                              help_text='The year for which you want the data')

    slug = 'assessor'
    name = "Assessor's Data"
    category = 'Finance'
    level = 'l'
    agency_type = 'Clerk'
    short_desc = 'Get the property values for your town.'

class FOIASalaryForm(FOIAWizardParent):
    """A form to fill in a salary template"""

    last_year = datetime.now().year - 1
    department = forms.CharField(help_text='Government department from which you '
                                           'want salary information')
    year = forms.IntegerField(min_value=1900, max_value=last_year, initial=last_year,
                              help_text='The year for which you want the data')

    slug = 'salary'
    name = 'Salary Data'
    category = 'Finance'
    level = 'l'
    agency_type = 'Finance'
    short_desc = 'Find out the salaries for positions in a government department.'

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
    agency_type = 'Clerk'
    short_desc = 'Find out what contracts companies are making with your government.'

class FOIABirthForm(FOIAWizardParent):
    """A form to fill in a birth certificate template"""

    full_name = forms.CharField(help_text='Full name of person whose birth record you want')
    birth_date = forms.DateField(label='Date of birth',
                                 widget=forms.TextInput(attrs={'class': 'datepicker'}))
    death_date = forms.DateField(label='Date of death',
                                 help_text='In many states, only individuals deceased for over 75 '
                                           'years have their records available for geneological '
                                           'inspection',
                                 widget=forms.TextInput(attrs={'class': 'datepicker'}))
    interest = forms.CharField(
            required=False,
            help_text='A brief sentence about your geneological interest in this individual',
            widget=forms.Textarea(attrs={'style': 'width:450px; height:32px'}))

    clean = validate_date_order('birth_date', 'death_date')

    slug = 'birth'
    name = 'Birth Record'
    category = 'Genealogy'
    level = 'l'
    agency_type = 'Health'
    short_desc = 'Get the birth certificate of a friend or family member.'

class FOIADeathForm(FOIAWizardParent):
    """A form to fill in a death certificate template"""

    full_name = forms.CharField(help_text='Full name of person whose death record you want')
    birth_date = forms.DateField(label='Date of birth',
                                 widget=forms.TextInput(attrs={'class': 'datepicker'}))
    death_date = forms.DateField(label='Date of death',
                                 help_text='In many states, only individuals deceased for over 75 '
                                           'years have their records available for geneological '
                                           'inspection',
                                 widget=forms.TextInput(attrs={'class': 'datepicker'}))
    interest = forms.CharField(
            required=False,
            help_text='A brief sentence about your geneological interest in this individual',
            widget=forms.Textarea(attrs={'style': 'width:450px; height:32px'}))

    clean = validate_date_order('birth_date', 'death_date')

    slug = 'death'
    name = 'Death Record'
    category = 'Genealogy'
    level = 'l'
    agency_type = 'Health'
    short_desc = 'Get the death certificate of a deceased friend or family member.'

class FOIAExpenseForm(FOIAWizardParent):
    """A form to fill in an expense report request template"""

    full_name = forms.CharField(help_text='Government employee you would like the emails of')
    department = forms.CharField(help_text='Department or office he or she is in')
    months_back = forms.IntegerField(help_text='How many months back')

    slug = 'expense'
    name = 'Expense Reports'
    category = 'Finance'
    level = 'lsf'
    agency_type = 'Finance'
    short_desc = 'Find out what the petty fund at your government is being spent on.'
    long_desc = 'This template was suggested by David Cuillier, Freedom of Information Committee '\
                'Chairman for the Society of Professional Journalists and Assistant Professor at '\
                'the School of Journalism at the University of Arizona.'

class FOIAMinutesForm(FOIAWizardParent):
    """A form to fill in a meeting minutes request template"""

    group = forms.CharField(help_text='Government group, board, or panel you want the minutes from')
    meetings_back = forms.IntegerField(help_text='How many meetings back')

    slug = 'minutes'
    name = 'Meeting Minutes'
    category = 'Bureaucracy'
    level = 'lsf'
    agency_type = 'Clerk'
    short_desc = 'Request the most recent minutes of a state agency, board or committee.'
    long_desc = 'This template was suggested by Barbara Croll Fought, associate professor at the '\
                'Newhouse School of Public Communications, Syracuse University.'

class FOIATravelForm(FOIAWizardParent):
    """A form to fill in a travel expense request template"""

    full_name = forms.CharField(help_text='Government employee you would like travel recipets from')
    department = forms.CharField(help_text='Department or office he or she is in')

    slug = 'travel'
    name = 'Travel Expense Reports'
    category = 'Finance'
    level = 'lsf'
    agency_type = 'Finance'
    short_desc = 'Discover how comfy your state employees are while roughing it on the road.'
    long_desc = 'This template was suggested by David Cuillier, Freedom of Information Committee '\
                'Chairman for the Society of Professional Journalists and Assistant Professor at '\
                'the School of Journalism at the University of Arizona.'

class FOIAAthleticForm(FOIAWizardParent):
    """A form to fill in an athletic personnel salary request template"""

    school = forms.CharField(help_text='School you would like the athletic personnel salaries for')

    slug = 'athletic'
    name = 'Athletic Personnel Salaries'
    category = 'Finance'
    level = 'ls'
    agency_type = 'Finance'
    short_desc = 'Unveil the salary information for school sports teams coaches, trainers and '\
                 'other support personnel.'
    long_desc = 'This template was suggested by Barbara Croll Fought, associate professor at the '\
                'Newhouse School of Public Communications, Syracuse University.'

class FOIAPetForm(FOIAWizardParent):
    """A form to fill in a pet license request template"""

    slug = 'pets'
    name = 'Pet Licensing Data'
    category = 'Health'
    level = 'l'
    agency_type = 'Health'
    short_desc = 'Discover which breeds are most popular, where dogs are most likely to be found '\
                 'in your city, and more.'
    long_desc = 'This template was suggested by David Cuillier, Freedom of Information Committee '\
                'Chairman for the Society of Professional Journalists and Assistant Professor at '\
                'the School of Journalism at the University of Arizona.'

class FOIAParkingForm(FOIAWizardParent):
    """A form to fill in a waived parking ticket template"""

    date_begin = forms.DateField(widget=forms.TextInput(attrs={'class': 'datepicker'}))
    date_end = forms.DateField(widget=forms.TextInput(attrs={'class': 'datepicker'}))

    clean = validate_date_order('date_begin', 'date_end')

    slug = 'parking'
    name = 'Parking Ticket Waivers'
    category = 'Crime'
    level = 'l'
    agency_type = 'Police'
    short_desc = "Discover who isn't paying their parking tickets, and who doesn't have to."
    long_desc = 'This template was suggested by David Cuillier, Freedom of Information Committee '\
                'Chairman for the Society of Professional Journalists and Assistant Professor at '\
                'the School of Journalism at the University of Arizona.'

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
    agency_type = 'Health'
    short_desc = 'Uncover how clean, or not, your favorite dining spots really are.'
    long_desc = 'This template was suggested by Will Sommer.'

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

    slug = 'sex'
    name = 'Sex Offender Registry'
    category = 'Crime'
    level = 'l'
    agency_type = 'Police'
    short_desc = "Receive your state's list of sex offenders."
    long_desc = 'This template was suggested by David Cuillier, Freedom of Information Committee '\
                'Chairman for the Society of Professional Journalists and Assistant Professor at '\
                'the School of Journalism at the University of Arizona.'

class FOIAFTCComplaintForm(FOIAWizardParent):
    """A form to fill in an FTC Complaint template"""

    companies = forms.CharField(
            label='Which company/companies',
            help_text='One per line',
            widget=forms.Textarea(attrs={'style': 'width:450px; height:80px'}))

    slug = 'ftc'
    name = 'FTC Complaint'
    category = 'Business'
    level = 'f'
    agency = 'FTC'
    short_desc = 'See all the complaints about a company or companies that '\
                 'have been filed with the Federal Trade Commission'

class FOIAMilitaryForm(FOIAWizardParent):
    """A form to fill in a Military Service Record template"""

    full_name = forms.CharField(help_text="The veteran's complete name while in service")
    service_number = forms.CharField(required=False)
    branch = forms.CharField(required=False, label='Branch of Service')
    date_begin = forms.DateField(widget=forms.TextInput(attrs={'class': 'datepicker'}),
                                 required=False, label='Date began service')
    date_end = forms.DateField(widget=forms.TextInput(attrs={'class': 'datepicker'}),
                               required=False, label='Date ended service')
    birth_date = forms.DateField(widget=forms.TextInput(attrs={'class': 'datepicker'}),
                                 required=False)
    birth_place = forms.CharField(required=False)
    entry = forms.CharField(required=False, label='Place of entry into the service')
    discharge = forms.CharField(required=False, label='Place of discharge')
    last_unit = forms.CharField(required=False, label='Last unit of assignment')
    reason = forms.CharField(required=False,
            help_text='The reason for your request, such as applying for veterans benefits, '
                      'preparing to retire, or researching your personal military history',
            widget=forms.Textarea(attrs={'style': 'width:450px; height:32px'}))

    slug = 'military'
    name = 'Military Service Record'
    category = 'Genealogy'
    level = 'f'
    agency_type = 'Clerk'
    short_desc = "Verify and individual's military service recors"
    long_desc = 'Please be advised that military service verification can be a very slow process'

class FOIABlankForm(FOIAWizardParent):
    """A form with no specific template"""

    title = forms.CharField(help_text='Be concise and descriptive', max_length=70,
                            widget=forms.TextInput(attrs={'style': 'width:450px'}))
    document_request = forms.CharField(
            help_text='One sentence describing the specific document you want',
            widget=forms.Textarea(attrs={'style': 'width:450px; height:32px'}))

    slug = 'none'
    name = 'Write My Own Request'
    category = 'None'
    level = 'lsf'
    agency_type = 'Clerk'

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

        template_file = 'request_templates/templates/%s.txt' % template
        data = form_list[2].cleaned_data if len(form_list) > 2 else {}
        data['jurisdiction'] = jurisdiction.name
        data['jurisdiction_template'] = \
                'request_templates/jurisdictions/%s.txt' % jurisdiction.legal()

        title, foia_request = \
            (s.strip() for s in render_to_string(template_file, data,
                                                 RequestContext(request)).split('\n', 1))

        agency = TEMPLATES[template].get_agency(jurisdiction)

        if len(title) > 70:
            title = title[:70]
        foia = FOIARequest.objects.create(user=request.user, status='started', title=title,
                                          jurisdiction=jurisdiction, slug=slugify(title),
                                          agency=agency)
        FOIACommunication.objects.create(
                foia=foia, from_who=request.user.get_full_name(), date=datetime.now(),
                response=False, full_html=False, communication=foia_request)

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
            if template.base_fields:
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


