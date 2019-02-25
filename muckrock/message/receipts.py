"""
Receipt objects for the messages app
"""

# Django
from django.conf import settings
from django.utils import timezone

# Standard Library
import logging
from datetime import datetime

# MuckRock
from muckrock.crowdfund.models import Crowdfund
from muckrock.foia.models import FOIARequest
from muckrock.message.email import TemplateEmail
from muckrock.organization.models import Organization

logger = logging.getLogger(__name__)

# move receipts to squarelet once crowdfunds and donations are moved over


class LineItem(object):
    """A line item for a receipt"""

    def __init__(self, name, price):
        if not isinstance(name, basestring):
            raise TypeError('Item name should be a string type')
        if not isinstance(price, int):
            # We basically want the cent representation of all our prices
            # e.g. $1.00 = 100 cents
            raise TypeError(
                'Price should be an integer of the smallest currency unit'
            )
        self.name = name
        self.price = price

    @property
    def formatted_price(self):
        """Formats a price for display."""
        return '$%.2f' % (self.price / 100.0)


class Receipt(TemplateEmail):
    """Our basic receipt sends an email to a user
    detailing a Stripe charge for a list of LineItems."""
    text_template = 'message/receipt/base.txt'
    html_template = 'message/receipt/base.html'

    def __init__(self, charge, items, **kwargs):
        # we assign charge and item to the instance first so
        # they can be used by the get_context_data method
        self.charge = charge
        if not isinstance(items, (list, tuple)):
            items = list(items)
        for item in items:
            if not isinstance(item, LineItem):
                raise TypeError(
                    'Each item in the list should be a receipt LineItem.'
                )
        self.items = items
        super(Receipt, self).__init__(**kwargs)
        # add additional receipt emails for this user
        if self.user:
            cc_emails = [r.email for r in self.user.receipt_emails.all()]
            self.cc.extend(cc_emails)
        # if no user provided, send the email to the address on the charge
        elif 'email' in self.charge.metadata:
            user_email = self.charge.metadata['email']
            self.to.append(user_email)
        else:
            raise ValueError('No user or email provided to receipt.')

    def get_context_data(self, *args):
        """Returns a dictionary of context for the template, given the charge object"""
        context = super(Receipt, self).get_context_data(*args)
        total = self.charge.amount / 100.0  # Stripe uses smallest-unit formatting
        context.update({
            'items': self.items,
            'total': total,
            'charge': {
                'id':
                    self.charge.id,
                'date':
                    datetime.fromtimestamp(
                        self.charge.created,
                        tz=timezone.get_current_timezone(),
                    ),
            }
        })
        if self.charge.source.object != 'bitcoin_receiver':
            context['charge'].update({
                'name': self.charge.source.name,
                'card': self.charge.source.brand,
                'last4': self.charge.source.last4,
            })
        return context


def generic_receipt(user, charge):
    """Generates a very basic receipt. Should be used as a fallback."""
    subject = u'Receipt'
    text = 'message/receipt/base.txt'
    html = 'message/receipt/base.html'
    item = LineItem('Payment', charge.amount)
    return Receipt(
        charge,
        [item],
        user=user,
        subject=subject,
        text_template=text,
        html_template=html,
    )


# XXX remove
def request_purchase_receipt(user, charge):
    """Generates a receipt for a request purchase and then returns it."""
    subject = u'Request Bundle Receipt'
    text = 'message/receipt/request_purchase.txt'
    html = 'message/receipt/request_purchase.html'
    num_requests = charge.metadata.get('amount')
    if num_requests:
        item_name = '{} requests'.format(num_requests)
    else:
        item_name = 'Requests'
    item = LineItem(item_name, charge.amount)
    return Receipt(
        charge,
        [item],
        user=user,
        subject=subject,
        text_template=text,
        html_template=html,
    )


# XXX remove
def request_fee_receipt(user, charge):
    """Generates a receipt for a payment of request fees."""
    subject = u'Request Fee Receipt'
    text = 'message/receipt/request_fees.txt'
    html = 'message/receipt/request_fees.html'
    amount = charge.amount
    agency_amount = int(amount / 1.05)
    muckrock_amount = amount - agency_amount
    items = [
        LineItem('Agency fee', agency_amount),
        LineItem('Processing fee', muckrock_amount),
    ]
    context = {}
    try:
        foia_pk = charge.metadata['foia']
        foia = FOIARequest.objects.get(pk=foia_pk)
        context.update({'foia': foia})
    except KeyError:
        logger.error('No FOIA identified in Charge metadata.')
    except FOIARequest.DoesNotExist:
        logger.error(
            'Could not find FOIARequest identified by Charge metadata.'
        )
    return Receipt(
        charge,
        items,
        user=user,
        subject=subject,
        extra_context=context,
        text_template=text,
        html_template=html,
    )


def crowdfund_payment_receipt(user, charge):
    """Generates a receipt for a payment on a crowdfund."""
    subject = u'Crowdfund Payment Receipt'
    text = 'message/receipt/crowdfund.txt'
    html = 'message/receipt/crowdfund.html'
    item = LineItem('Crowdfund Payment', charge.amount)
    context = {}
    try:
        crowdfund_pk = charge.metadata['crowdfund_id']
        crowdfund = Crowdfund.objects.get(pk=crowdfund_pk)
        context.update({'crowdfund': crowdfund})
    except KeyError:
        logger.error('No Crowdfund identified in Charge metadata.')
    except Crowdfund.DoesNotExist:
        logger.error('Could not find Crowdfund identified by Charge metadata.')
    return Receipt(
        charge,
        [item],
        user=user,
        subject=subject,
        extra_context=context,
        text_template=text,
        html_template=html,
    )


# XXX remove
def pro_subscription_receipt(user, charge):
    """Generates a receipt for a payment on a pro account."""
    subject = u'Professional Account Receipt'
    text = 'message/receipt/pro_subscription.txt'
    html = 'message/receipt/pro_subscription.html'
    item = LineItem('Professional Account', charge.amount)
    context = {'monthly_requests': settings.MONTHLY_REQUESTS['pro']}
    return Receipt(
        charge,
        [item],
        user=user,
        subject=subject,
        extra_context=context,
        text_template=text,
        html_template=html,
    )


# XXX remove
def org_subscription_receipt(user, charge):
    """Generates a receipt for a payment on an org account."""
    subject = u'Organization Account Receipt'
    text = 'message/receipt/org_subscription.txt'
    html = 'message/receipt/org_subscription.html'
    item = LineItem('Organization Account', charge.amount)
    try:
        context = {'org': Organization.objects.get(owner=user)}
    except Organization.DoesNotExist:
        logger.warning('Org receipt generated for non-owner User.')
        context = {'org': None}
    return Receipt(
        charge,
        [item],
        user=user,
        subject=subject,
        extra_context=context,
        text_template=text,
        html_template=html,
    )


def donation_receipt(user, charge):
    """Generates a receipt for a donation."""
    subject = u'Donation Receipt'
    text = 'message/receipt/donation.txt'
    html = 'message/receipt/donation.html'
    item = LineItem('Tax Deductible Donation', charge.amount)
    return Receipt(
        charge,
        [item],
        user=user,
        subject=subject,
        text_template=text,
        html_template=html,
    )
