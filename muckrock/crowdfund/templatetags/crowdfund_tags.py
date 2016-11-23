"""
Nodes and tags for rendering crowdfunds into templates
"""

from django import template
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404

from muckrock.crowdfund.models import Crowdfund
from muckrock.crowdfund.forms import CrowdfundPaymentForm
from muckrock.utils import cache_get_or_set

register = template.Library()

def list_to_english_string(the_list):
    """A utility function to convert a list into an English string"""
    # convert list items to strings and remove empty strings
    str_list = [str(each_item) for each_item in the_list if str(each_item)]
    num_str = len(str_list)
    ret_str = ''
    # base case is that the list is empty
    if num_str == 0:
        return ret_str
    # construct an English list based on the number of items
    last_str = str_list[num_str - 1]
    if num_str == 1:
        ret_str = last_str
    elif num_str == 2:
        ret_str = str_list[0] + ' and ' + last_str
    else:
        sans_last_str = str_list[:num_str - 1]
        ret_str = (', ').join(sans_last_str) + ', and ' + last_str
    return ret_str

def get_initial_amount(crowdfund):
    """Dynamically compute an initial amount for the payment form."""
    initial_amount = 2500
    amount_remaining = int(crowdfund.amount_remaining() * 100)
    if crowdfund.payment_capped and amount_remaining < initial_amount:
        initial_amount = amount_remaining
    return initial_amount

def crowdfund_form(crowdfund, form):
    """Returns a form initialized with crowdfund data"""
    initial_data = {
        'show': True,
        'crowdfund': crowdfund.pk,
        'stripe_amount': get_initial_amount(crowdfund)
    }
    return form(initial=initial_data)

def crowdfund_user(context):
    """Returns a tuple of user information"""
    logged_in = context['user'].is_authenticated()
    user_email = context['user'].email if logged_in else ''
    return (logged_in, user_email)

def contributor_summary(named_contributors, contributors_count, anonymous):
    """Returns a summary of the contributors to the project"""
    contributor_names = [x.get_full_name() for x in named_contributors]
    unnamed_string = ''
    named_limit = 4
    num_unnamed = len(contributor_names) - named_limit
    # prevents num_unnamed from being a negative value
    num_unnamed = 0 if num_unnamed < 0 else num_unnamed
    if anonymous > 0 or num_unnamed > 0:
        unnamed_string = str(num_unnamed + anonymous)
        # if named and unnamed together, use 'other/others'
        if len(contributor_names) > 0:
            unnamed_string += ' other'
            if (anonymous + num_unnamed) > 1:
                unnamed_string += 's'
        # if only unnamed, use 'person/people'
        else:
            if (anonymous + num_unnamed) > 1:
                unnamed_string += ' people'
            else:
                unnamed_string += ' person'
    if contributors_count > 0:
        summary = ('Backed by '
                   + list_to_english_string(contributor_names[:named_limit] + [unnamed_string])
                   + '.')
    else:
        summary = 'No backers yet. Be the first!'
    return summary

def generate_crowdfund_context(the_crowdfund, the_url_name, the_form, the_context):
    """Generates context in a way that's agnostic towards the object being crowdfunded."""
    endpoint = reverse(the_url_name, kwargs={'pk': the_crowdfund.pk})
    payment_form = crowdfund_form(the_crowdfund, the_form)
    logged_in, user_email = crowdfund_user(the_context)
    the_request = the_context.request
    named, contrib_count, anon_count = (
            cache_get_or_set(
                'cf:%s:crowdfund_widget_data' % the_crowdfund.pk,
                lambda: (
                    list(the_crowdfund.named_contributors()),
                    the_crowdfund.contributors_count(),
                    the_crowdfund.anonymous_contributors_count(),
                    ),
                settings.DEFAULT_CACHE_TIMEOUT))
    contrib_sum = contributor_summary(
            named,
            contrib_count,
            anon_count)
    obj_url = the_crowdfund.get_crowdfund_object().get_absolute_url()
    return {
        'crowdfund': the_crowdfund,
        'named_contributors': named,
        'contributors_count': contrib_count,
        'anon_contributors_count': anon_count,
        'contributor_summary': contrib_sum,
        'endpoint': endpoint,
        'login_form': AuthenticationForm(),
        'logged_in': logged_in,
        'user_email': user_email,
        'payment_form': payment_form,
        'request': the_request,
        'stripe_pk': settings.STRIPE_PUB_KEY,
        'obj_url': obj_url,
    }

@register.inclusion_tag('crowdfund/widget.html', name='crowdfund', takes_context=True)
def crowdfund_tag(context, crowdfund_pk=None, crowdfund=None):
    """Template tag to insert a crowdfunding widget"""
    if crowdfund is None:
        crowdfund = get_object_or_404(Crowdfund, pk=crowdfund_pk)
    return generate_crowdfund_context(
        crowdfund,
        'crowdfund',
        CrowdfundPaymentForm,
        context
    )
