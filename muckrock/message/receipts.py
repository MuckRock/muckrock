"""
Receipt objects for the messages app
"""

from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from datetime import datetime

from muckrock.foia.models import FOIARequest

class GenericReceipt(EmailMultiAlternatives):
    """A basic receipt"""
    subject = u'Your Receipt'
    item = u''
    text_template = 'message/receipt/receipt.txt'

    def __init__(self, user, charge, **kwargs):
        super(GenericReceipt, self).__init__(**kwargs)
        if isinstance(user, User):
            self.user = user
            self.to = [user.email]
        else:
            self.user = None
            try:
                user_email = charge['metadata']['email']
                self.to = [user_email]
            except KeyError:
                self.to = []
        self.from_email = 'MuckRock <info@muckrock.com>'
        self.bcc = ['diagnostics@muckrock.com']
        self.body = render_to_string(
            self.get_text_template(),
            self.get_context_data(charge)
        )

    def get_text_template(self):
        """Returns a plain text email template reference"""
        return self.text_template

    def get_context_data(self, charge):
        """Returns a dictionary of context for the template, given the charge object"""
        amount = charge['amount'] / 100.0 # Stripe uses smallest-unit formatting
        card = charge['source']
        return {
            'user': self.user,
            'id': charge['id'],
            'date': datetime.fromtimestamp(charge['created']),
            'item': self.item,
            'last4': card['last4'],
            'amount': amount
        }


class RequestPurchaseReceipt(GenericReceipt):
    """A receipt for request purchases"""
    subject = u'Payment received for additional requests'
    item = u'4 requests'
    text_template = 'message/receipt/request_purchase.txt'


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
            foia_pk = charge['metadata']['foia']
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
    text_template = 'message/receipt/multirequest.txt'


class CrowdfundPaymentReceipt(GenericReceipt):
    """A receipt for the payment to a crowdfund"""
    subject = u'Payment received for crowdfunding a request'
    item = u'Crowdfund payment'
    text_template = 'message/receipt/crowdfund.txt'


class ProSubscriptionReceipt(GenericReceipt):
    """A receipt for a recurring pro subscription charge"""
    subject = u'Payment received for professional account'
    item = u'Professional subscription'
    text_template = 'message/receipt/pro.txt'


class OrgSubscriptionReceipt(GenericReceipt):
    """A receipt for a recurring org subscription charge"""
    subject = u'Payment received dor organization account'
    item = u'Organization subscription'
    text_template = 'message/receipt/org.txt'
