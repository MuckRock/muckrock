# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task', '0011_auto_20160228_1056'),
        ('crowdfund', '0013_auto_20160215_1119'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='crowdfundproject',
            name='project',
        ),
        migrations.RemoveField(
            model_name='crowdfundprojectpayment',
            name='crowdfund',
        ),
        migrations.RemoveField(
            model_name='crowdfundprojectpayment',
            name='user',
        ),
        migrations.RemoveField(
            model_name='crowdfundrequest',
            name='foia',
        ),
        migrations.RemoveField(
            model_name='crowdfundrequestpayment',
            name='crowdfund',
        ),
        migrations.RemoveField(
            model_name='crowdfundrequestpayment',
            name='user',
        ),
        migrations.DeleteModel(
            name='CrowdfundProject',
        ),
        migrations.DeleteModel(
            name='CrowdfundProjectPayment',
        ),
        migrations.DeleteModel(
            name='CrowdfundRequest',
        ),
        migrations.DeleteModel(
            name='CrowdfundRequestPayment',
        ),
    ]
