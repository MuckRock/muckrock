"""
Nodes and tags for rendering crowdfunds into templates
"""

from django import template
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404

from muckrock.crowdfund.models import CrowdfundProject, CrowdfundRequest
from muckrock.crowdfund.forms import CrowdfundRequestPaymentForm, CrowdfundProjectPaymentForm
from muckrock.settings import STRIPE_PUB_KEY

register = template.Library()

def crowdfund_form(crowdfund, form):
    """Returns a form initialized with crowdfund data"""
    initial_data = {'crowdfund': crowdfund.pk}
    default_amount = 25
    if crowdfund.amount_remaining() < default_amount:
        initial_data['amount'] = int(crowdfund.amount_remaining()) * 100
    else:
        initial_data['amount'] = default_amount * 100
    return form(initial=initial_data)

def crowdfund_user(context):
    """Returns a tuple of user information"""
    logged_in = context['user'].is_authenticated()
    user_email = context['user'].email if logged_in else ''
    return (logged_in, user_email)

def generate_crowdfund_context(the_crowdfund, the_url_name, the_form, the_context):
    """Generates context in a way that's agnostic towards the object being crowdfunded."""
    endpoint = reverse(the_url_name, kwargs={'pk': the_crowdfund.pk})
    payment_form = crowdfund_form(the_crowdfund, the_form)
    logged_in, user_email = crowdfund_user(the_context)
    return {
        'crowdfund': the_crowdfund,
        'endpoint': endpoint,
        'logged_in': logged_in,
        'user_email': user_email,
        'payment_form': payment_form,
        'stripe_pk': STRIPE_PUB_KEY
    }

@register.inclusion_tag('crowdfund/widget.html', takes_context=True)
def crowdfund_request(context, crowdfund_pk):
    """Template tag to insert a crowdfunding panel"""
    the_crowdfund = get_object_or_404(CrowdfundRequest, pk=crowdfund_pk)
    return generate_crowdfund_context(
        the_crowdfund,
        'crowdfund-request',
        CrowdfundRequestPaymentForm,
        context
    )

@register.inclusion_tag('crowdfund/widget.html', takes_context=True)
def crowdfund_project(context, crowdfund_pk):
    """Template tag to insert a crowdfunding widget"""
    the_crowdfund = get_object_or_404(CrowdfundProject, pk=crowdfund_pk)
    return generate_crowdfund_context(
        the_crowdfund,
        'crowdfund-project',
        CrowdfundProjectPaymentForm,
        context
    )
