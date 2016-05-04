"""
Receipt objects for the messages app
"""

from django.conf import settings

from datetime import datetime
import logging

from muckrock.foia.models import FOIARequest
from muckrock.message.email import TemplateEmail
from muckrock.organization.models import Organization

logger = logging.getLogger(__name__)

class Receipt(TemplateEmail):
    """Our basic receipt sends an email to a user detailing a Stripe charge for an item."""
    text_template = 'message/receipt/base.txt'
    html_template = 'message/receipt/base.html'

    def __init__(self, charge, item, **kwargs):
        # we assign charge and item to the instance first so
        # they can be used by the get_context_data method
        self.charge = charge
        self.item = item
        super(Receipt, self).__init__(**kwargs)
        # if no user provided, send the email to the address on the charge
        if not self.user:
            try:
                user_email = self.charge.metadata['email']
                self.to.append(user_email)
            except KeyError:
                raise ValueError('No user or email provided to receipt.')

    def get_context_data(self, *args):
        """Returns a dictionary of context for the template, given the charge object"""
        context = super(Receipt, self).get_context_data(*args)
        total = self.charge.amount / 100.0 # Stripe uses smallest-unit formatting
        line_items = [{
            'name': self.item,
            'price': amount,
        }]
        return {
            'line_items': line_items,
            'total': total,
            'charge': {
                'id': self.charge.id,
                'name': self.charge.source.name,
                'date': datetime.fromtimestamp(self.charge.created),
                'card': self.charge.source.brand,
                'last4': self.charge.source.last4,
            }
        }


class RequestPurchaseReceipt(Receipt):
    """A receipt for request purchases"""
    subject = u'Payment received for additional requests'
    item = u'4 requests'
    text_template = 'message/receipt/request_purchase.txt'

    def get_context_data(self, charge):
        """Adjusts the item description to account for variable request purchase amounts"""
        context = super(RequestPurchaseReceipt, self).get_context_data(charge)
        if self.user:
            bundle_size = settings.BUNDLED_REQUESTS.get(self.user.profile.acct_type, 4)
            item = unicode(bundle_size) + u' requests'
            context['item'] = item
        return context


class RequestFeeReceipt(Receipt):
    """A receipt for payment of request fees"""
    subject = u'Payment received for request fee'
    item = u'Request fee'
    text_template = 'message/receipt/request_fees.txt'

    def get_context_data(self, charge):
        """Returns the context for the template"""
        context = super(RequestFeeReceipt, self).get_context_data(charge)
        amount = context['amount']
        base_amount = amount / 1.05
        fee_amount = amount - base_amount
        context['base_amount'] = base_amount
        context['fee_amount'] = fee_amount
        try:
            foia_pk = charge.metadata['foia']
            foia = FOIARequest.objects.get(pk=foia_pk)
            context['url'] = foia.get_absolute_url()
        except KeyError:
            logger.error('No FOIA identified in Charge metadata.')
        except FOIARequest.DoesNotExist:
            logger.error('Could not find FOIARequest identified by Charge metadata.')
        return context


class MultiRequestReceipt(Receipt):
    """A receipt for the purchase of a multirequest"""
    subject = u'Payment received for multi request fee'
    item = u'Multi-request fee'
    text_template = 'message/receipt/request_multi.txt'


class CrowdfundPaymentReceipt(Receipt):
    """A receipt for the payment to a crowdfund"""
    subject = u'Payment received for crowdfunding a request'
    item = u'Crowdfund payment'
    text_template = 'message/receipt/crowdfund.txt'


class ProSubscriptionReceipt(Receipt):
    """A receipt for a recurring pro subscription charge"""
    subject = u'Payment received for professional account'
    item = u'Professional subscription'
    text_template = 'message/receipt/pro_subscription.txt'

    def get_context_data(self, charge):
        """Add monthly requests to context"""
        context = super(ProSubscriptionReceipt, self).get_context_data(charge)
        context['monthly_requests'] = settings.MONTHLY_REQUESTS['pro']
        return context


class OrgSubscriptionReceipt(Receipt):
    """A receipt for a recurring org subscription charge"""
    subject = u'Payment received dor organization account'
    item = u'Organization subscription'
    text_template = 'message/receipt/org_subscription.txt'

    def get_context_data(self, charge):
        """Add the organization to the context"""
        context = super(OrgSubscriptionReceipt, self).get_context_data(charge)
        context['org'] = Organization.objects.get(owner=self.user)
        return context
