"""
Views for the crowdfund application
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

import logging
import stripe
import sys

from muckrock.crowdfund.models import CrowdfundRequest, CrowdfundProject, \
                                      CrowdfundRequestPayment, CrowdfundProjectPayment
from muckrock.crowdfund.forms import CrowdfundPayForm
from muckrock.foia.models import FOIARequest
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.settings import STRIPE_SECRET_KEY, STRIPE_PUB_KEY

logger = logging.getLogger(__name__)
stripe.api_key = STRIPE_SECRET_KEY

def _contribute(request, crowdfund, payment_model, redirect_url):
    """Contribute to a crowdfunding request or project"""
    
    if request.method == 'POST':
        form = CrowdfundPayForm(request.POST, request=request)

        if form.is_valid():
            try:
                amount = form.cleaned_data['amount']
                user_profile = request.user.get_profile()
                user_profile.pay(form, int(amount * 100), 'Contribute to Crowdfunding: %s %s' %
                                                     (crowdfund, crowdfund.pk))
                crowdfund.payment_received += amount
                crowdfund.save()
                payment_model.objects.create(user=request.user, crowdfund=crowdfund, amount=amount)
                messages.success(request, 'You have succesfully contributed $%.2f' % amount)
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
def contribute_request(request, jurisdiction, jidx, slug, idx):
    """Contribute to a crowdfunding request"""

    jmodel = get_object_or_404(Jurisdiction, slug=jurisdiction, pk=jidx)
    foia = get_object_or_404(FOIARequest, jurisdiction=jmodel, slug=slug, pk=idx)
    crowdfund = get_object_or_404(CrowdfundRequest,  foia=foia)
    if crowdfund.expired():
        raise Http404()

    def redirect_url(crowdfund):
        """Redirect to the FOIA detail page"""
        return reverse('foia-detail',
            kwargs={'jurisdiction': crowdfund.foia.jurisdiction.slug,
                    'jidx': crowdfund.foia.jurisdiction.pk,
                    'slug': crowdfund.foia.slug,
                    'idx': crowdfund.foia.pk})

    return _contribute(request, crowdfund, CrowdfundRequestPayment, redirect_url)

@login_required
def contribute_project(request, idx):
    """Contribute to a crowdfunding project"""

    crowdfund = get_object_or_404(CrowdfundProject, pk=idx)

    def redirect_url(crowdfund):
        """Redirect to the Project detail page"""
        return reverse('project-detail',
            kwargs={'slug': crowdfund.project.slug,
                    'idx': crowdfund.project.pk})

    return _contribute(request, crowdfund, CrowdfundProjectPayment, redirect_url)

def project_detail(request, slug, idx):
    """Project details"""

    project = get_object_or_404(CrowdfundProject, slug=slug, pk=idx)

    return render_to_response('crowdfund/project_detail.html', {'project': project},
                              context_instance=RequestContext(request))
