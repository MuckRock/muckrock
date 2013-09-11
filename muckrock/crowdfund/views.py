"""
Views for the crowdfund application
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.views.generic.detail import DetailView

import logging
import stripe
import sys

from muckrock.crowdfund.models import CrowdfundRequest, CrowdfundProject, \
                                      CrowdfundRequestPayment, CrowdfundProjectPayment
from muckrock.crowdfund.forms import CrowdfundPayForm
from muckrock.settings import STRIPE_SECRET_KEY, STRIPE_PUB_KEY

logger = logging.getLogger(__name__)
stripe.api_key = STRIPE_SECRET_KEY

#class ProjectDetail(DetailView):
#    """Detail View for a Project"""
#    model = Project

def _contribute(request, pk, cf_model, payment_model, redirect_url):
    """Contribute to a crowdfunding request or project"""
    
    crowdfund = get_object_or_404(cf_model, pk=pk)

    if request.method == 'POST':
        form = CrowdfundPayForm(request.POST, request=request)

        if form.is_valid():
            try:
                amount = form.cleaned_data['amount']
                user_profile = request.user.get_profile()
                user_profile.pay(form, amount * 100, 'Contribute to Crowdfunding')
                crowdfund.payment_received += amount
                crowdfund.save()
                payment_model.create(request.user, crowdfund, amount)
                messages.success(request, 'You have succesfully contributed %.2f' % amount)
                logger.info('%s has contributed to crowdfund',  request.user.username)
            except stripe.CardError as exc:
                messages.error(request, 'Payment error: %s' % exc)
                logger.error('Payment error: %s', exc, exc_info=sys.exc_info())

            return HttpResponseRedirect(redirect_url(crowdfund))

    else:
        form = CrowdfundPayForm(request=request, initial={'name': request.user.get_full_name()})

    return render_to_response('registration/cc.html',
                              {'form': form, 'pub_key': STRIPE_PUB_KEY, 'heading': 'Contribute',
                               'desc': 'Contribute to a crowdfunded request.'},
                              context_instance=RequestContext(request))

@login_required
def contribute_request(request, pk):
    """Contribute to a crowdfunding request"""

    def redirect_url(crowdfund):
        """Redirect to the FOIA detail page"""
        return reverse('foia-detail',
            kwargs={'jurisdiction': crowdfund.foia.jurisdiction.slug,
                    'jidx': crowdfund.foia.jurisdiction.pk,
                    'slug': crowdfund.foia.slug,
                    'idx': crowdfund.foia.pk})

    return _contribute(request, pk, CrowdfundRequest, CrowdfundRequestPayment, redirect_url)

@login_required
def contribute_project(request, pk):
    """Contribute to a crowdfunding project"""

    def redirect_url(crowdfund):
        """Redirect to the Project detail page"""
        return reverse('project-detail',
            kwargs={'slug': crowdfund.project.slug,
                    'idx': crowdfund.project.pk})

    return _contribute(request, pk, CrowdfundProject, CrowdfundProjectPayment, redirect_url)

def project_detail(request, slug, pk):
    """Project details"""

    project = get_object_or_404(Project, slug=slug, pk=pk)

    return render_to_response('crowdfund/project_detail.html', {'project': project})
