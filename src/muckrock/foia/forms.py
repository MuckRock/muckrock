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

from foia.models import FOIARequest, JURISDICTIONS
from foia.utils import make_template_choices
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


class FOIAMugShotForm(forms.Form):
    """A form to fill in a mug shot template"""

    full_name = forms.CharField(help_text='Full name of person whose mug shots you want')
    date_begin = forms.DateField(help_text='Range of dates in which the mug shots were taken',
                                 widget=CalendarWidget(attrs={'class': 'datepicker'}))
    date_end = forms.DateField(widget=CalendarWidget(attrs={'class': 'datepicker'}))


class FOIAAssessorForm(forms.Form):
    """A form to fill in a assessor template"""

    last_year = datetime.now().year - 1

    location = forms.CharField(help_text='County or town from which you want assessor information')
    year = forms.IntegerField(min_value=1900, max_value=last_year, initial=last_year,
                              help_text='The year for which you want the data')


class FOIABlankForm(forms.Form):
    """A form with no specific template"""

    title = forms.CharField(help_text='Be concise and descriptive', max_length=70,
                            widget=forms.TextInput(attrs={'style': 'width:450px'}))
    document_request = forms.CharField(
            help_text='One sentence describing the specific document you want',
            widget=forms.Textarea(attrs={'style': 'width:450px; height:32px'}))

Template = namedtuple('Template', 'id, name, category, form')
TEMPLATES = {
    'mug_shot': Template('mug_shot', 'Mug Shots',       'Crime', FOIAMugShotForm),
    'assessor': Template('assessor', "Assessor's Data", 'Money', FOIAAssessorForm),
    'none':     Template('none',     'None',            None,    FOIABlankForm),
    }

TEMPLATE_CHOICES = make_template_choices(TEMPLATES)


class FOIAWizardStartForm(forms.Form):
    """A form to select which FOIA template you want"""

    template = forms.ChoiceField(choices=TEMPLATE_CHOICES)
    jurisdiction = forms.ChoiceField(choices=JURISDICTIONS)
    max_pay = forms.IntegerField(label='What will you pay for the request?',
                                 help_text="We'll cover the first $5",
                                 min_value=5, initial=5,
                                 widget=forms.TextInput(attrs={'size': 2}))
    public_interest = forms.BooleanField(label='Is this request in the public interest?',
                                         help_text="If it is, fees might be waived",
                                         initial=True, required=False)
    name_attached = forms.BooleanField(label='Attach your name to the request?',
                                       initial=True, required=False)


class FOIAWizard(FormWizard):
    """Wizard to create FOIA requests"""

    def done(self, request, form_list):
        """Wizard has been completed"""

        template = form_list[0].cleaned_data['template']
        jurisdiction = form_list[0].cleaned_data['jurisdiction']
        template_file = 'request_templates/%s.txt' % template
        data = form_list[0].cleaned_data
        data.update(form_list[1].cleaned_data)

        title, foia_request = (s.strip() for s in
                               render_to_string(template_file, data,
                                                RequestContext(request)).split('\n', 1))
        # need to set agency!

        if len(title) > 70:
            title = title[:70]
        FOIARequest.objects.create(user=request.user, status='started',
                                   jurisdiction=jurisdiction, title=title,
                                   request=foia_request, slug=slugify(title))

        messages.success(request, 'Request succesfully created.  Please review it and make any '
                                  'changes that you need.  You may save it for future review or '
                                  'submit it when you are ready.')

        return HttpResponseRedirect(reverse('foia-update',
                                    kwargs={'jurisdiction': jurisdiction,
                                            'user_name': request.user.username,
                                            'slug': slugify(title)}))

    def process_step(self, request, form, step):
        """Process each step"""

        if self.determine_step(request) == 0 and step == 0:
            template = TEMPLATES[form.cleaned_data['template']]
            self.extra_context = {'heading': template.name}
            if len(self.form_list) == 1:
                self.form_list.append(template.form)
            elif len(self.form_list) == 2:
                # state may be saved if they start over without finishing
                self.form_list[1] = template.form
            elif len(self.form_list) > 2:
                # error, this should never happen
                pass

    def get_template(self, step):
        """Template name"""

        return 'foia/foiawizard_form.html'

