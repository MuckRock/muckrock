"""
Receipt objects for the messages app
"""

from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from datetime import datetime

class GenericReceipt(EmailMultiAlternatives):
    """A basic receipt"""
    subject = u'Your Receipt'
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
            'last4': card['last4'],
            'amount': amount
        }


class RequestPurchaseReceipt(GenericReceipt):
    """A receipt for request purchases"""
    subject = u'Payment received for additional requests'
    text_template = 'message/receipt/request_purchase.txt'

class RequestFeeReceipt(GenericReceipt):
    """A receipt for payment of request fees"""
    subject = u'Payment received for request fee'
    text_template = 'message/receipt/request_fees.txt'

    def get_context_data(self, charge):
        """Returns the context for the template"""
        context = super(RequestFeeReceipt, self).get_context_data(charge)
        amount = context['amount']
        base_amount = amount / 1.05
        fee_amount = amount - base_amount
        context['base_amount'] = base_amount
        context['fee_amount'] = fee_amount
        return context

class MultiRequestReceipt(GenericReceipt):
    """A receipt for the purchase of a multirequest"""
    subject = u'Payment received for multi request fee'
    text_template = 'message/receipt/multirequest.txt'

class CrowdfundPaymentReceipt(GenericReceipt):
    """A receipt for the payment to a crowdfund"""
    subject = u'Payment received for crowdfunding a request'
    text_template = 'message/receipt/crowdfund.txt'

class ProSubscriptionReceipt(GenericReceipt):
    """A receipt for a recurring pro subscription charge"""
    subject = u'Payment received for professional account'
    text_template = 'message/receipt/pro.txt'

class OrgSubscriptionReceipt(GenericReceipt):
    """A receipt for a recurring org subscription charge"""
    subject = u'Payment received dor organization account'
    text_template = 'message/receipt/org.txt'
