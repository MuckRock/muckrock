# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('foia', '0001_initial'),
        ('crowdfund', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='foias',
            field=models.ManyToManyField(related_name='foias', null=True, to='foia.FOIARequest', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='crowdfundrequestpayment',
            name='crowdfund',
            field=models.ForeignKey(related_name='payments', to='crowdfund.CrowdfundRequest'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='crowdfundrequestpayment',
            name='user',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='crowdfundrequest',
            name='foia',
            field=models.OneToOneField(related_name='crowdfund', to='foia.FOIARequest'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='crowdfundprojectpayment',
            name='crowdfund',
            field=models.ForeignKey(to='crowdfund.CrowdfundProject'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='crowdfundprojectpayment',
            name='user',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='crowdfundproject',
            name='payments',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, through='crowdfund.CrowdfundProjectPayment'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='crowdfundproject',
            name='project',
            field=models.OneToOneField(related_name='crowdfund', to='crowdfund.Project'),
            preserve_default=True,
        ),
    ]
