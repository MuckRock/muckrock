"""
Models for the crowdfund application
"""

from django.db import models

class CrowdfundRequest(models.Model):
    """Keep track of crowdfunding for a request"""

    foia = models.OneToOneField('foia.FOIARequest', related_name='crowdfund')
    payment_required = models.DecimalField(max_digits=8, decimal_places=2, default='0.00')
    payment_received = models.DecimalField(max_digits=8, decimal_places=2, default='0.00')


class Project(models.Model):
    """A project involving multiple FOIA Requests"""

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    description = models.TextField(blank=True)
    foias = models.ManyToManyField(FOIARequest, related_name='foias', blank=True, null=True)


class CrowdfundProject(models.Model):
    """Keep track of crowdfunding for a project"""

    project = models.OneToOneField(Project, related_name='crowdfund')
    payment_required = models.DecimalField(max_digits=8, decimal_places=2, default='0.00')
    payment_received = models.DecimalField(max_digits=8, decimal_places=2, default='0.00')

