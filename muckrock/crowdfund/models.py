"""
Models for the crowdfund application
"""

from django.contrib.auth.models import User
from django.db import models


class CrowdfundABC(models.Model):
    """Abstract base class for crowdfunding objects"""
    payment_required = models.DecimalField(max_digits=8, decimal_places=2, default='0.00')
    payment_received = models.DecimalField(max_digits=8, decimal_places=2, default='0.00')
    date_due = models.DateField()

    class Meta:
        abstract = True


class CrowdfundPaymentABC(models.Model):
    """Abstract base class for crowdfunding objects"""
    user = models.ForeignKey(User)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class CrowdfundRequest(CrowdfundABC):
    """Keep track of crowdfunding for a request"""

    foia = models.OneToOneField('foia.FOIARequest', related_name='crowdfund')
    payments = models.ManyToManyField(User, through='CrowdfundRequestPayment')


class CrowdfundRequestPayment(CrowdfundPaymentABC):
    """M2M intermediate model"""
    crowdfund = models.ForeignKey(CrowdfundRequest)


class Project(models.Model):
    """A project involving multiple FOIA Requests"""

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    description = models.TextField(blank=True)
    foias = models.ManyToManyField('foia.FOIARequest', related_name='foias', blank=True, null=True)


class CrowdfundProject(Crowdfund):
    """Keep track of crowdfunding for a project"""

    project = models.OneToOneField(Project, related_name='crowdfund')
    payments = models.ManyToManyField(User, through='CrowdfundProjectPayment')


class CrowdfundProjectPayment(CrowdfundPaymentABC):
    """M2M intermediate model"""
    crowdfund = models.ForeignKey(CrowdfundProject)
