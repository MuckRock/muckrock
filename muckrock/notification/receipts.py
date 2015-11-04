"""
Receipt objects for the notification app
"""

from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

class GenericReceipt(EmailMultiAlternatives):
    """A basic receipt"""
    def __init__(self, user, charge, **kwargs):
        super(FailedPaymentNotification, self).__init__(**kwargs)
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
        self.subject = self.get_subject()
        self.body = render_to_string(
            self.get_text_template(),
            self.get_context_data(charge)
        )

    def get_subject(self):
        """Returns a receipt-appropriate subject"""
        return u'Your Receipt'

    def get_text_template(self):
        """Returns a plain text email template reference"""
        return 'notification/receipt/receipt.txt'

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
    def get_subject(self):
        return u'Payment received for additional requests'

    def get_text_template(self):
        return 'notification/receipt/request_purchase.txt'

class RequestFeeReceipt(GenericReciept):
    """A receipt for payment of request fees"""
    def get_subject(self):
        return u'Payment received for request fee'

    def get_text_template(self):
        return 'notification/receipt/request_fees.txt'

    def get_context_data(self, charge):
        """Returns the context for the template"""
        context = super(RequestFeeReceipt, self).get_context_data(charge)
        amount = context['amount']
        context['base_amount'] = amount / 1.05
        context['fee_amount'] = amount - base_amount
        return context

class MultiRequestReceipt(GenericReceipt):
    """A receipt for the purchase of a multirequest"""
    def get_subject(self):
        return u'Payment received for multi request fee'

    def get_text_tempalte(self):
        return 'notification/receipt/multirequest.txt'

class CrowdfundPaymentReceipt(GenericReceipt):
    """A receipt for the payment to a crowdfund"""
    def get_subject(self):
        return u'Payment received for crowdfunding a request'

    def get_text_template(self):
        return 'notification/receipt/crowdfund.txt'

class ProSubscriptionReceipt(GenericReceipt):
    """A receipt for a recurring pro subscription charge"""
    def get_subject(self):
        return u'Payment received for professional account'

    def get_text_template(self):
        return 'notification/receipt/pro.txt'

class OrgSubscriptionReceipt(GenericReceipt):
    """A receipt for a recurring org subscription charge"""
    def get_subject(self):
        return u'Payment received dor organization account'

    def get_text_template(self):
        return 'notification/receipt/org.txt'
