# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0014_auto_20160120_1644'),
    ]

    operations = [
        migrations.AddField(
            model_name='statistics',
            name='daily_requests_admin',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='statistics',
            name='daily_requests_org',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='statistics',
            name='daily_requests_proxy',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='statistics',
            name='total_active_org_members',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='statistics',
            name='total_active_orgs',
            field=models.IntegerField(null=True, blank=True),
        ),
    ]
