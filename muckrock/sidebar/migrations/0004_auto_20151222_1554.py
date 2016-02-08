# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('sidebar', '0003_auto_20151104_2115'),
    ]

    operations = [
        migrations.AddField(
            model_name='broadcast',
            name='updated',
            field=models.DateTimeField(default=datetime.datetime(2015, 12, 22, 15, 54, 42, 639798), auto_now=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='broadcast',
            name='context',
            field=models.CharField(unique=True, max_length=255, choices=[(b'admin', b'Admin'), (b'basic', b'Basic'), (b'beta', b'Beta'), (b'pro', b'Professional'), (b'proxy', b'Proxy'), (b'robot', b'Robot'), (b'anonymous', b'Visitor')]),
        ),
    ]
