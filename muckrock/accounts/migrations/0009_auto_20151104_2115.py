# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_statistics_requests_processing_days'),
    ]

    operations = [
        migrations.AddField(
            model_name='statistics',
            name='daily_robot_response_tasks',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='acct_type',
            field=models.CharField(max_length=10, choices=[(b'admin', b'Admin'), (b'beta', b'Beta'), (b'community', b'Community'), (b'pro', b'Professional'), (b'proxy', b'Proxy'), (b'robot', b'Robot')]),
        ),
    ]
