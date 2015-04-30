"""
Models for the crowdfund application
"""

from django.contrib.auth.models import User
from django.db import models

from datetime import date


class CrowdfundABC(models.Model):
    """Abstract base class for crowdfunding objects"""
    # pylint: disable=R0903, model-missing-unicode
    payment_required = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default='0.00'
    )
    payment_received = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default='0.00'
    )
    date_due = models.DateField()

    def expired(self):
        """Has this crowdfuning run out of time?"""
        return date.today() >= self.date_due

    class Meta:
        abstract = True

class CrowdfundPaymentABC(models.Model):
    """Abstract base class for crowdfunding objects"""
    # pylint: disable=R0903, model-missing-unicode
    user = models.ForeignKey(User, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    show = models.BooleanField(default=False)

    class Meta:
        abstract = True

class CrowdfundRequest(CrowdfundABC):
    """Keep track of crowdfunding for a request"""
    foia = models.OneToOneField('foia.FOIARequest', related_name='crowdfund')
    payments = models.ManyToManyField(User, through='CrowdfundRequestPayment')

    def __unicode__(self):
        # pylint: disable=E1101
        return 'Crowdfunding for %s' % self.foia.title

class CrowdfundRequestPayment(CrowdfundPaymentABC):
    """M2M intermediate model"""
    crowdfund = models.ForeignKey(CrowdfundRequest)

    def __unicode__(self):
        # pylint: disable=E1101
        return 'Payment of $%.2f by %s on %s for %s' % \
            (self.amount, self.user, self.date.date(), self.crowdfund.foia)

class Project(models.Model):
    """A project involving multiple FOIA Requests"""
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    description = models.TextField(blank=True)
    foias = models.ManyToManyField(
        'foia.FOIARequest',
        related_name='foias',
        blank=True,
        null=True
    )

    def __unicode__(self):
        return self.name

class CrowdfundProject(CrowdfundABC):
    """Keep track of crowdfunding for a project"""
    project = models.OneToOneField(Project, related_name='crowdfund')
    payments = models.ManyToManyField(User, through='CrowdfundProjectPayment')

    def __unicode__(self):
        return self.project.name

class CrowdfundProjectPayment(CrowdfundPaymentABC):
    """M2M intermediate model"""
    # pylint: disable=model-missing-unicode
    crowdfund = models.ForeignKey(CrowdfundProject)
