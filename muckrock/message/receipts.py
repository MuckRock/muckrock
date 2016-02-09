"""
Receipt objects for the messages app
"""

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from datetime import datetime
import logging

from muckrock.foia.models import FOIARequest
from muckrock.organization.models import Organization

logger = logging.getLogger(__name__)

class GenericReceipt(EmailMultiAlternatives):
    """A basic receipt"""
    item = u''
    text_template = 'message/receipt/base.txt'
    subject = u'Your Receipt'

    def __init__(self, user, charge, **kwargs):
        super(GenericReceipt, self).__init__(subject=self.subject, **kwargs)
        if isinstance(user, User):
            self.user = user
            self.to = [user.email]
        else:
            self.user = None
            try:
                user_email = charge.metadata['email']
                self.to = [user_email]
            except KeyError:
                self.to = []
        self.from_email = 'MuckRock <info@muckrock.com>'
        self.bcc = ['diagnostics@muckrock.com']
        self.body = render_to_string(
            self.text_template,
            self.get_context_data(charge)
        )

    def get_context_data(self, charge):
        """Returns a dictionary of context for the template, given the charge object"""
        amount = charge.amount / 100.0 # Stripe uses smallest-unit formatting
        card = charge.source
        return {
            'user': self.user,
            'id': charge.id,
            'date': datetime.fromtimestamp(charge.created),
            'item': self.item,
            'last4': card.get('last4'),
            'amount': amount
        }


class RequestPurchaseReceipt(GenericReceipt):
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


class RequestFeeReceipt(GenericReceipt):
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


class MultiRequestReceipt(GenericReceipt):
    """A receipt for the purchase of a multirequest"""
    subject = u'Payment received for multi request fee'
    item = u'Multi-request fee'
    text_template = 'message/receipt/request_multi.txt'


class CrowdfundPaymentReceipt(GenericReceipt):
    """A receipt for the payment to a crowdfund"""
    subject = u'Payment received for crowdfunding a request'
    item = u'Crowdfund payment'
    text_template = 'message/receipt/crowdfund.txt'


class ProSubscriptionReceipt(GenericReceipt):
    """A receipt for a recurring pro subscription charge"""
    subject = u'Payment received for professional account'
    item = u'Professional subscription'
    text_template = 'message/receipt/pro_subscription.txt'

    def get_context_data(self, charge):
        """Add monthly requests to context"""
        context = super(ProSubscriptionReceipt, self).get_context_data(charge)
        context['monthly_requests'] = settings.MONTHLY_REQUESTS['pro']
        return context


class OrgSubscriptionReceipt(GenericReceipt):
    """A receipt for a recurring org subscription charge"""
    subject = u'Payment received dor organization account'
    item = u'Organization subscription'
    text_template = 'message/receipt/org_subscription.txt'

    def get_context_data(self, charge):
        """Add the organization to the context"""
        context = super(OrgSubscriptionReceipt, self).get_context_data(charge)
        context['org'] = Organization.objects.get(owner=self.user)
        return context
