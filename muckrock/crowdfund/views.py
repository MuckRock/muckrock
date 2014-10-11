"""
Views for the crowdfund application
"""

from django.contrib import messages
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
                desc = 'Contribute to Crowdfunding: %s %s' % (crowdfund, crowdfund.pk)
                if request.user.is_authenticated():
                    user_profile = request.user.get_profile()
                    user_profile.pay(form, int(amount * 100), desc)
                    user = request.user
                else:
                    desc = '%s: %s' % (form.cleaned_data.get('email'), desc)
                    stripe.Charge.create(amount=int(amount * 100), currency='usd',
                        card=form.cleaned_data.get('token'), description=desc)
                    user = None
                payment_model.objects.create(user=user, crowdfund=crowdfund, amount=amount,
                    name=form.cleaned_data.get('display_name'),
                    show=form.cleaned_data.get('show'))
                crowdfund.payment_received += amount
                crowdfund.save()
                messages.success(request, 'You contributed $%.2f. Thanks!' % amount)
                logger.info('%s has contributed to crowdfund', request.user.username)
            except stripe.CardError as exc:
                messages.error(request, 'Payment error: %s' % exc)
                logger.error('Payment error: %s', exc, exc_info=sys.exc_info())

            return HttpResponseRedirect(redirect_url(crowdfund))

    else:
        name = request.user.get_full_name() if request.user.is_authenticated() else ''
        form = CrowdfundPayForm(request=request, initial={'name': name, 'display_name': name})

    context = {
        'form': form,
        'pub_key': STRIPE_PUB_KEY,
        'heading': 'Contribute',
        'desc': 'Contribute to a crowdfunded request.'
    }
    return render_to_response(
        'forms/account/cc.html',
        context,
        context_instance=RequestContext(request)
    )

def contribute_request(request, jurisdiction, jidx, slug, idx):
    """Contribute to a crowdfunding request"""

    jmodel = get_object_or_404(Jurisdiction, slug=jurisdiction, pk=jidx)
    foia = get_object_or_404(FOIARequest, jurisdiction=jmodel, slug=slug, pk=idx)
    crowdfund = get_object_or_404(CrowdfundRequest, foia=foia)
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

    return render_to_response(
        'crowdfund/project_detail.html',
        { 'project': project },
        context_instance=RequestContext(request)
    )
