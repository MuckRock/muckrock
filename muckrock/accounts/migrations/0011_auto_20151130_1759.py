# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0010_merge'),
    ]

    operations = [
        migrations.RenameField(
            model_name='statistics',
            old_name='daily_requests_community',
            new_name='daily_requests_basic',
        ),
        migrations.AlterField(
            model_name='profile',
            name='acct_type',
            field=models.CharField(max_length=10, choices=[(b'admin', b'Admin'), (b'basic', b'Basic'), (b'beta', b'Beta'), (b'pro', b'Professional'), (b'proxy', b'Proxy'), (b'robot', b'Robot')]),
        ),
    ]
