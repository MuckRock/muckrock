# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sidebar', '0002_auto_20150717_1142'),
    ]

    operations = [
        migrations.AlterField(
            model_name='broadcast',
            name='context',
            field=models.CharField(unique=True, max_length=255, choices=[(b'admin', b'Admin'), (b'beta', b'Beta'), (b'community', b'Community'), (b'pro', b'Professional'), (b'proxy', b'Proxy'), (b'robot', b'Robot'), (b'anonymous', b'Visitor')]),
        ),
    ]
