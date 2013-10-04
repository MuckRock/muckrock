"""
Wizards for the FOIA application
"""

from django.contrib import messages
from django.contrib.formtools.wizard.views import SessionWizardView
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string, get_template
from django.template import RequestContext

from datetime import datetime
import HTMLParser
import logging

from muckrock.agency.models import Agency
from muckrock.foia.forms import TEMPLATES 
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.foia.models import FOIARequest, FOIAMultiRequest, FOIACommunication
from muckrock.settings import STRIPE_PUB_KEY
from muckrock.utils import get_node

logger = logging.getLogger(__name__)

class SubmitMultipleWizard(SessionWizardView):
    """Wizard to submit a request to multiple agencies"""
    # pylint: disable=R0904

    templates = {
        'submit': 'foia/foiarequest_submit_multiple.html',
        'agency': 'foia/foiarequest_confirm_multiple.html',
        'pay':    'foia/foiarequest_pay_multiple.html',
        'nopay':  'foia/foiarequest_pay_multiple.html',
    }
    agencies = None

    def done(self, form_list, **kwargs):
        """Pay for extra requests if necessary and then file all the requests"""

        foia = get_object_or_404(FOIAMultiRequest, slug=kwargs['slug'], pk=kwargs['idx'])

        data = self.get_all_cleaned_data()
        agencies = data['agencies']
        user = self.request.user
        profile = user.get_profile()

        # handle # requests and payment
        request_dict = profile.multiple_requests(agencies.count())
        profile.monthly_requests -= request_dict['monthly_requests']
        profile.num_requests -= request_dict['reg_requests']
        profile.save()
        payment_required = 400 * request_dict['extra_requests']

        if payment_required > 0:
            profile.pay(form_list[-1], payment_required,
                        'Charge for multi request: %s %s' % (foia.title, foia.pk))
            logger.info('%s has paid %0.2f for request %s',
                        user.username, payment_required/100, foia.title)

        # mark to be filed
        foia.agencies = agencies
        foia.status = 'submitted'
        foia.save()
        messages.success(self.request, 'Request has been submitted to selected agencies')
        send_mail('[MULTI] Freedom of Information Request: %s' % (foia.title),
                  render_to_string('foia/multi_mail.txt', {'request': foia}),
                  'info@muckrock.com', ['requests@muckrock.com'], fail_silently=False)

        # redirect to your foias
        return HttpResponseRedirect(reverse('foia-mylist', kwargs={'view': 'all'}))

    def get_template_names(self):
        return self.templates[self.steps.current]

    def _get_agencies(self):
        """Get and cache the agncies selected in the submit step"""
        if self.agencies:
            return self.agencies
        else:
            data = self.get_cleaned_data_for_step('submit')
            if not data:
                return None
            agency_type = data.get('agency_type')
            jurisdiction = data.get('jurisdiction')
            agencies = Agency.objects.all()
            if agency_type:
                agencies = agencies.filter(types=agency_type)
            if jurisdiction and jurisdiction.level == 's':
                agencies = agencies.filter(Q(jurisdiction=jurisdiction) |
                                           Q(jurisdiction__parent=jurisdiction))
            elif jurisdiction:
                agencies = agencies.filter(jurisdiction=jurisdiction)
            self.agencies = agencies
            return agencies

    def get_form_kwargs(self, step=None):
        if step == 'agency':
            return {'queryset': self._get_agencies()}
        elif step == 'pay':
            return {'request': self.request}
        else:
            return {}

    def get_form_initial(self, step):
        if step == 'agency':
            return {'agencies': self._get_agencies()}
        elif step == 'pay':
            return {'name': self.request.user.get_full_name()}
        else:
            return self.initial_dict.get(step, {})

    def get_context_data(self, form, **kwargs):
        """Add extra context to certain steps"""
        context = super(SubmitMultipleWizard, self).get_context_data(form=form, **kwargs)
        if self.steps.current in ['pay', 'nopay']:
            data = self.get_cleaned_data_for_step('agency')
            num_requests = data['agencies'].count()
            extra_context = self.request.user.get_profile().multiple_requests(num_requests)
            extra_context['payment_required'] = 4 * extra_context['extra_requests']
            extra_context['pub_key'] = STRIPE_PUB_KEY
            context.update(extra_context)
        return context


class FOIAWizard(SessionWizardView):
    """Wizard to create FOIA requests"""
    # pylint: disable=R0904

    def done(self, form_list):
        """Wizard has been completed"""
        # pylint: disable=R0914

        data = self.get_all_cleaned_data()

        template_name = data['template']

        level = data['level']
        if level == 'local' or level == 'state':
            jurisdiction = data[level]
        elif level == 'federal':
            jurisdiction = Jurisdiction.objects.get(level='f')
        elif level == 'multi':
            jurisdiction = None

        template_file = 'request_templates/%s.txt' % template_name
        data['jurisdiction'] = jurisdiction

        template = get_template(template_file)
        context = RequestContext(self.request, data)
        requested_docs = get_node(template, context, 'content')
        # unescape the content from the template
        html_parser = HTMLParser.HTMLParser()
        requested_docs = html_parser.unescape(requested_docs)

        title, foia_request = \
            (s.strip() for s in template.render(context).split('\n', 1))

        agency = TEMPLATES[template_name].get_agency(jurisdiction)

        if len(title) > 70:
            title = title[:70]
        slug = slugify(title) or 'untitled'
        if jurisdiction:
            foia = FOIARequest.objects.create(user=self.request.user, status='started', title=title,
                                              jurisdiction=jurisdiction, slug=slug,
                                              agency=agency, requested_docs=requested_docs,
                                              description=requested_docs)
            FOIACommunication.objects.create(
                    foia=foia, from_who=self.request.user.get_full_name(), to_who=foia.get_to_who(),
                    date=datetime.now(), response=False, full_html=False,
                    communication=foia_request)
        else:
            foia = FOIAMultiRequest.objects.create(user=self.request.user, title=title, slug=slug,
                                                   requested_docs=requested_docs, status='started')

        messages.success(self.request, 'Request succesfully created.  Please review it and make '
                                       'any changes that you need.  You may save it for future '
                                       'review or submit it when you are ready.')

        if jurisdiction:
            return HttpResponseRedirect(reverse('foia-update',
                                        kwargs={'jurisdiction': jurisdiction.slug,
                                                'jidx': jurisdiction.pk,
                                                'idx': foia.pk,
                                                'slug': slug}))
        else:
            return HttpResponseRedirect(reverse('foia-multi-update',
                                        kwargs={'idx': foia.pk, 'slug': slug}))

    def get_context_data(self, form, **kwargs):
        """Add extra context to certain steps"""
        context = super(FOIAWizard, self).get_context_data(form=form, **kwargs)
        if self.steps.index == 2:
            template = TEMPLATES[self.get_all_cleaned_data().get('template')]
            context.update({'heading': template.name})
        return context

    def get_template_names(self):
        """Template name"""

        if self.steps.current == 'FOIAWizardWhereForm':
            return 'foia/foiawizard_where.html'
        elif self.steps.current.startswith('FOIAWhat'):
            return 'foia/foiawizard_what.html'
        else:
            return 'foia/foiawizard_form.html'

